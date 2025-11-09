/**
 * ARK Rate Limiting Middleware
 * 
 * Implements rate limiting for ARK API using Redis or in-memory storage
 */

const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG_PATH = path.join(process.env.ARK_HOME || process.cwd(), 'config', 'rate-limit.json');
let config = loadConfig();

// Storage adapters
let storage;

/**
 * Load rate limiting configuration
 */
function loadConfig() {
    try {
        if (fs.existsSync(CONFIG_PATH)) {
            return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
        }
    } catch (error) {
        console.error('Failed to load rate limit config:', error.message);
    }
    
    // Default configuration
    return {
        enabled: false,
        strategy: 'sliding-window',
        storage: 'memory',
        limits: {
            default: {
                requests: 100,
                window: 60
            }
        },
        whitelist: ['127.0.0.1', '::1'],
        blacklist: [],
        headers: {
            total: 'X-RateLimit-Limit',
            remaining: 'X-RateLimit-Remaining',
            reset: 'X-RateLimit-Reset'
        }
    };
}

/**
 * Redis Storage Adapter
 */
class RedisStorage {
    constructor(redisClient) {
        this.redis = redisClient;
    }
    
    async increment(key, window) {
        const now = Date.now();
        const windowStart = now - (window * 1000);
        
        // Remove old entries
        await this.redis.zremrangebyscore(key, 0, windowStart);
        
        // Count current requests
        const count = await this.redis.zcard(key);
        
        // Add new request
        await this.redis.zadd(key, now, `${now}-${Math.random()}`);
        
        // Set expiration
        await this.redis.expire(key, window * 2);
        
        return count + 1;
    }
    
    async get(key) {
        return await this.redis.zcard(key);
    }
    
    async reset(key) {
        await this.redis.del(key);
    }
}

/**
 * In-Memory Storage Adapter
 */
class MemoryStorage {
    constructor() {
        this.store = new Map();
        this.cleanupInterval = setInterval(() => this.cleanup(), 60000);
    }
    
    async increment(key, window) {
        const now = Date.now();
        const windowStart = now - (window * 1000);
        
        if (!this.store.has(key)) {
            this.store.set(key, []);
        }
        
        const requests = this.store.get(key);
        
        // Remove old requests
        const validRequests = requests.filter(timestamp => timestamp > windowStart);
        
        // Add new request
        validRequests.push(now);
        this.store.set(key, validRequests);
        
        return validRequests.length;
    }
    
    async get(key) {
        const requests = this.store.get(key) || [];
        return requests.length;
    }
    
    async reset(key) {
        this.store.delete(key);
    }
    
    cleanup() {
        const now = Date.now();
        const maxAge = 3600000; // 1 hour
        
        for (const [key, requests] of this.store.entries()) {
            const validRequests = requests.filter(timestamp => now - timestamp < maxAge);
            if (validRequests.length === 0) {
                this.store.delete(key);
            } else {
                this.store.set(key, validRequests);
            }
        }
    }
}

/**
 * Initialize storage adapter
 */
function initStorage() {
    if (config.storage === 'redis') {
        try {
            const redis = require('redis');
            const client = redis.createClient({
                host: process.env.ARK_REDIS_HOST || '127.0.0.1',
                port: parseInt(process.env.ARK_REDIS_PORT || '6379')
            });
            
            client.on('error', (err) => {
                console.error('Redis error:', err.message);
                console.log('Falling back to memory storage');
                storage = new MemoryStorage();
            });
            
            client.on('ready', () => {
                console.log('Rate limiting using Redis');
            });
            
            storage = new RedisStorage(client);
        } catch (error) {
            console.error('Failed to initialize Redis:', error.message);
            console.log('Using memory storage for rate limiting');
            storage = new MemoryStorage();
        }
    } else {
        storage = new MemoryStorage();
        console.log('Rate limiting using memory storage');
    }
}

/**
 * Get client IP address
 */
function getClientIP(req) {
    return req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
           req.headers['x-real-ip'] ||
           req.connection?.remoteAddress ||
           req.socket?.remoteAddress ||
           'unknown';
}

/**
 * Check if IP is whitelisted
 */
function isWhitelisted(ip) {
    return config.whitelist.includes(ip) || 
           config.whitelist.some(pattern => {
               if (pattern.includes('*')) {
                   const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
                   return regex.test(ip);
               }
               return false;
           });
}

/**
 * Check if IP is blacklisted
 */
function isBlacklisted(ip) {
    return config.blacklist.includes(ip);
}

/**
 * Get rate limit for endpoint
 */
function getRateLimit(req) {
    // Check for specific endpoint limits
    for (const [name, limit] of Object.entries(config.limits)) {
        if (name !== 'default' && req.path.startsWith(`/${name}`)) {
            return limit;
        }
    }
    
    return config.limits.default;
}

/**
 * Rate limiting middleware
 */
async function rateLimitMiddleware(req, res, next) {
    // Skip if disabled
    if (!config.enabled || process.env.ARK_RATE_LIMIT_ENABLED === 'false') {
        return next();
    }
    
    // Initialize storage if needed
    if (!storage) {
        initStorage();
    }
    
    const ip = getClientIP(req);
    
    // Check blacklist
    if (isBlacklisted(ip)) {
        return res.status(403).json({
            error: 'Forbidden',
            message: 'Your IP has been blocked'
        });
    }
    
    // Check whitelist
    if (isWhitelisted(ip)) {
        return next();
    }
    
    // Get rate limit for this endpoint
    const limit = getRateLimit(req);
    const key = `ratelimit:${ip}:${req.path}`;
    
    try {
        // Increment counter
        const count = await storage.increment(key, limit.window);
        
        // Calculate reset time
        const resetTime = Math.floor(Date.now() / 1000) + limit.window;
        
        // Set rate limit headers
        res.setHeader(config.headers.total, limit.requests);
        res.setHeader(config.headers.remaining, Math.max(0, limit.requests - count));
        res.setHeader(config.headers.reset, resetTime);
        
        // Check if limit exceeded
        if (count > limit.requests) {
            return res.status(429).json({
                error: 'Too Many Requests',
                message: limit.message || 'Rate limit exceeded',
                retryAfter: limit.window
            });
        }
        
        next();
    } catch (error) {
        console.error('Rate limit error:', error);
        // On error, allow the request (fail open)
        next();
    }
}

/**
 * Rate limit status endpoint
 */
function rateLimitStatus(req, res) {
    const ip = getClientIP(req);
    
    res.json({
        enabled: config.enabled,
        ip: ip,
        whitelisted: isWhitelisted(ip),
        blacklisted: isBlacklisted(ip),
        limits: config.limits
    });
}

// Export middleware
module.exports = rateLimitMiddleware;
module.exports.status = rateLimitStatus;
module.exports.reload = () => { config = loadConfig(); };
