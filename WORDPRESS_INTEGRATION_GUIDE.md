# 🌐 ARK Integration with WordPress (1true.org)

**Goal:** Make your ARK chat interface accessible through 1true.org  
**Date:** 2025-11-09

---

## 🎯 **Integration Options**

### **Option 1: Embed via iFrame** ⭐ EASIEST
**Best for:** Quick integration, minimal setup  
**Effort:** 5 minutes  
**Technical Level:** Beginner

### **Option 2: Subdomain Proxy** ⭐ RECOMMENDED
**Best for:** Professional setup, better performance  
**Effort:** 15-30 minutes  
**Technical Level:** Intermediate

### **Option 3: WordPress Plugin with API**
**Best for:** Deep integration, WordPress feel  
**Effort:** 1-2 hours  
**Technical Level:** Advanced

### **Option 4: Full Frontend Deployment**
**Best for:** Complete control, custom domain  
**Effort:** 30-60 minutes  
**Technical Level:** Intermediate-Advanced

---

## 🚀 **OPTION 1: iFrame Embed (Quickest)**

### **Step 1: Deploy ARK to a Public Server**

You need ARK running on a publicly accessible server. Options:

#### **A. Use Current Sandbox (Temporary)**
Your current URL (expires with sandbox):
```
https://4173-iqvk5326f1xsbwmwb3rnw-d0b9e1e2.sandbox.novita.ai
```

#### **B. Deploy to Cloud (Permanent)**
- **Vercel** (Free tier): Best for frontend
- **Railway** (Free tier): Best for full stack
- **Heroku** (Free tier): Traditional option
- **DigitalOcean** ($4/mo): Best for control
- **AWS/GCP/Azure**: Enterprise option

---

### **Step 2: Create WordPress Page**

1. **Login to WordPress Admin**
   - Go to: https://1true.org/wp-admin

2. **Create New Page**
   - Pages → Add New
   - Title: "ARK Assistant" or "AI Chat"

3. **Add iFrame Code**

**Using Block Editor (Gutenberg):**
- Click the `+` button
- Search for "Custom HTML" block
- Paste this code:

```html
<!-- ARK Chat Interface Embed -->
<div class="ark-embed-container">
    <iframe 
        src="YOUR_ARK_URL_HERE" 
        width="100%" 
        height="800px" 
        frameborder="0" 
        allow="microphone; camera; geolocation"
        style="border: none; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
    </iframe>
</div>

<style>
.ark-embed-container {
    max-width: 1200px;
    margin: 20px auto;
    padding: 20px;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .ark-embed-container iframe {
        height: 600px;
    }
}
</style>
```

**Replace `YOUR_ARK_URL_HERE` with:**
- Temporary: `https://4173-iqvk5326f1xsbwmwb3rnw-d0b9e1e2.sandbox.novita.ai`
- Permanent: Your deployed URL (see deployment section below)

4. **Publish Page**
   - Click "Publish" button
   - Access at: https://1true.org/ark-assistant

---

### **Enhanced iFrame with Loading State**

```html
<div class="ark-embed-container">
    <div id="ark-loading" class="ark-loading">
        <div class="spinner"></div>
        <p>Loading ARK System...</p>
    </div>
    
    <iframe 
        id="ark-frame"
        src="YOUR_ARK_URL_HERE" 
        width="100%" 
        height="800px" 
        frameborder="0" 
        allow="microphone; camera; geolocation"
        onload="document.getElementById('ark-loading').style.display='none'"
        style="border: none; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
    </iframe>
</div>

<style>
.ark-embed-container {
    max-width: 1200px;
    margin: 20px auto;
    padding: 20px;
    position: relative;
}

.ark-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    z-index: 10;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #00e0ff;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Mobile responsive */
@media (max-width: 768px) {
    .ark-embed-container iframe {
        height: 600px;
    }
}
</style>
```

---

## 🌐 **OPTION 2: Subdomain Proxy (RECOMMENDED)**

### **Best Setup:**
- Main site: https://1true.org
- ARK interface: https://ark.1true.org or https://chat.1true.org

### **Benefits:**
- Professional appearance
- Better performance
- No iFrame limitations
- Full screen experience
- Better SEO

---

### **Step 1: Deploy ARK to Cloud**

#### **A. Deploy to Vercel (Recommended for Frontend)**

1. **Install Vercel CLI:**
```bash
npm install -g vercel
```

2. **Prepare Frontend for Deployment:**
```bash
cd /home/user/webapp/frontend

# Update vite.config.js for production
cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: 'dist',
    emptyOutDir: true
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
EOF
```

3. **Build and Deploy:**
```bash
# Build
npm run build

# Deploy to Vercel
cd dist
vercel --prod
```

4. **Get Deployment URL:**
Vercel will give you a URL like: `https://ark-frontend-xyz.vercel.app`

---

#### **B. Deploy Backend to Railway**

1. **Create Railway Account:**
   - Go to: https://railway.app
   - Sign up with GitHub

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your ark repository

3. **Configure Service:**
   - Add environment variables if needed
   - Set start command: `node intelligent-backend.cjs`
   - Railway will assign a URL: `https://ark-backend-xyz.railway.app`

---

### **Step 2: Configure DNS for Subdomain**

1. **Access Domain DNS Settings:**
   - Login to your domain registrar (where you bought 1true.org)
   - Find DNS management section

2. **Add CNAME Record:**

**For Frontend on Vercel:**
```
Type: CNAME
Name: ark (or chat)
Value: cname.vercel-dns.com
TTL: 3600
```

**Alternative - A Record (if you have a static IP):**
```
Type: A
Name: ark
Value: YOUR_SERVER_IP
TTL: 3600
```

3. **Configure in Vercel/Railway:**
   - Go to project settings
   - Add custom domain: `ark.1true.org`
   - Vercel will verify and issue SSL certificate

4. **Wait for Propagation:**
   - DNS changes take 5 minutes to 48 hours
   - Usually works within 15-30 minutes

---

### **Step 3: Update WordPress Menu**

1. **Add Menu Item:**
   - WordPress Admin → Appearance → Menus
   - Add Custom Link:
     - URL: `https://ark.1true.org`
     - Link Text: "ARK Assistant" or "AI Chat"
   - Save Menu

2. **Or Create Button in Page:**
```html
<a href="https://ark.1true.org" 
   class="ark-button" 
   target="_blank"
   style="
       display: inline-block;
       padding: 15px 30px;
       background: linear-gradient(135deg, #00e0ff, #0080ff);
       color: white;
       text-decoration: none;
       border-radius: 8px;
       font-weight: bold;
       box-shadow: 0 4px 15px rgba(0,224,255,0.3);
       transition: all 0.3s ease;
   "
   onmouseover="this.style.transform='translateY(-2px)'"
   onmouseout="this.style.transform='translateY(0)'">
   🌌 Launch ARK Assistant
</a>
```

---

## 🔧 **OPTION 3: WordPress Plugin Integration**

### **Create Custom Plugin for Deep Integration**

**File:** `wp-content/plugins/ark-chat/ark-chat.php`

```php
<?php
/**
 * Plugin Name: ARK Chat Assistant
 * Description: Integrates ARK AI assistant into WordPress
 * Version: 1.0
 * Author: Your Name
 */

// Prevent direct access
if (!defined('ABSPATH')) exit;

// Add shortcode for embedding
function ark_chat_shortcode($atts) {
    $atts = shortcode_atts(array(
        'height' => '800px',
        'width' => '100%',
    ), $atts);
    
    $ark_url = get_option('ark_chat_url', 'https://your-ark-url.com');
    
    ob_start();
    ?>
    <div class="ark-chat-embed">
        <iframe 
            src="<?php echo esc_url($ark_url); ?>"
            width="<?php echo esc_attr($atts['width']); ?>"
            height="<?php echo esc_attr($atts['height']); ?>"
            frameborder="0"
            style="border: none; border-radius: 10px;">
        </iframe>
    </div>
    <style>
    .ark-chat-embed {
        max-width: 1200px;
        margin: 20px auto;
    }
    </style>
    <?php
    return ob_get_clean();
}
add_shortcode('ark_chat', 'ark_chat_shortcode');

// Add settings page
function ark_chat_settings_page() {
    add_options_page(
        'ARK Chat Settings',
        'ARK Chat',
        'manage_options',
        'ark-chat-settings',
        'ark_chat_settings_page_html'
    );
}
add_action('admin_menu', 'ark_chat_settings_page');

function ark_chat_settings_page_html() {
    if (!current_user_can('manage_options')) return;
    
    if (isset($_POST['ark_chat_url'])) {
        update_option('ark_chat_url', sanitize_text_field($_POST['ark_chat_url']));
        echo '<div class="updated"><p>Settings saved!</p></div>';
    }
    
    $ark_url = get_option('ark_chat_url', '');
    ?>
    <div class="wrap">
        <h1>ARK Chat Settings</h1>
        <form method="post">
            <table class="form-table">
                <tr>
                    <th scope="row">ARK URL</th>
                    <td>
                        <input type="url" 
                               name="ark_chat_url" 
                               value="<?php echo esc_attr($ark_url); ?>"
                               class="regular-text"
                               placeholder="https://your-ark-url.com">
                        <p class="description">Enter the URL where your ARK system is hosted</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
        
        <h2>Usage</h2>
        <p>Add this shortcode to any page or post:</p>
        <code>[ark_chat]</code>
        
        <p>Or with custom dimensions:</p>
        <code>[ark_chat width="100%" height="600px"]</code>
    </div>
    <?php
}

// Add floating chat button
function ark_chat_floating_button() {
    $ark_url = get_option('ark_chat_url', '');
    if (empty($ark_url)) return;
    ?>
    <div id="ark-floating-button" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
    ">
        <a href="<?php echo esc_url($ark_url); ?>" 
           target="_blank"
           style="
               display: flex;
               align-items: center;
               justify-content: center;
               width: 60px;
               height: 60px;
               background: linear-gradient(135deg, #00e0ff, #0080ff);
               border-radius: 50%;
               box-shadow: 0 4px 20px rgba(0,224,255,0.4);
               text-decoration: none;
               font-size: 30px;
               transition: all 0.3s ease;
           "
           onmouseover="this.style.transform='scale(1.1)'"
           onmouseout="this.style.transform='scale(1)'">
            🌌
        </a>
    </div>
    <?php
}
add_action('wp_footer', 'ark_chat_floating_button');
?>
```

**Usage:**
1. Create the plugin file
2. Activate in WordPress Admin → Plugins
3. Configure URL in Settings → ARK Chat
4. Use shortcode `[ark_chat]` in any page/post

---

## 🚀 **OPTION 4: Full Frontend Deployment**

### **Deploy ARK Frontend to Your WordPress Hosting**

If you have SSH access to your WordPress hosting:

```bash
# 1. Build frontend locally
cd /home/user/webapp/frontend
npm run build

# 2. Upload to WordPress server
# Create subdirectory in WordPress
ssh user@your-server.com
mkdir -p /var/www/html/ark

# 3. Upload built files
scp -r dist/* user@your-server.com:/var/www/html/ark/

# 4. Configure Apache/Nginx to serve /ark path
```

**Apache Configuration (.htaccess):**
```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /ark/
    RewriteRule ^index\.html$ - [L]
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule . /ark/index.html [L]
</IfModule>
```

**Access at:** https://1true.org/ark

---

## 📋 **RECOMMENDED DEPLOYMENT PATH**

### **For 1true.org - Step by Step:**

#### **Phase 1: Quick Test (Today)**
1. Use current sandbox URL in iFrame
2. Test on a draft WordPress page
3. Verify functionality

#### **Phase 2: Deploy Frontend (This Week)**
1. Deploy frontend to Vercel (free, fast)
2. Deploy backend to Railway (free tier)
3. Connect with subdomain: `ark.1true.org`

#### **Phase 3: Polish (Next Week)**
1. Add custom styling to match 1true.org theme
2. Create WordPress plugin for easy management
3. Add floating chat button site-wide

---

## 🎨 **Styling to Match 1true.org**

### **Custom CSS for iFrame Integration:**

```html
<style>
/* ARK Embed Styling for 1true.org */
.ark-embed-container {
    background: #0a0a0f;
    padding: 40px 20px;
    margin: 40px auto;
    max-width: 1400px;
    border-radius: 20px;
    box-shadow: 0 10px 50px rgba(0,0,0,0.5);
}

.ark-header {
    text-align: center;
    margin-bottom: 30px;
}

.ark-header h2 {
    color: #00e0ff;
    font-size: 2.5em;
    margin-bottom: 10px;
    text-shadow: 0 0 20px rgba(0,224,255,0.5);
}

.ark-header p {
    color: #888;
    font-size: 1.2em;
}

.ark-frame-wrapper {
    position: relative;
    overflow: hidden;
    border-radius: 15px;
    box-shadow: 0 0 30px rgba(0,224,255,0.2);
}

iframe {
    display: block;
    border: none;
}

/* Responsive */
@media (max-width: 768px) {
    .ark-embed-container {
        padding: 20px 10px;
    }
    
    .ark-header h2 {
        font-size: 1.8em;
    }
    
    iframe {
        height: 600px !important;
    }
}
</style>

<div class="ark-embed-container">
    <div class="ark-header">
        <h2>🌌 ARK Assistant</h2>
        <p>Your AI Council of Consciousness</p>
    </div>
    
    <div class="ark-frame-wrapper">
        <iframe 
            src="YOUR_ARK_URL" 
            width="100%" 
            height="800" 
            frameborder="0">
        </iframe>
    </div>
</div>
```

---

## 🔐 **Security Considerations**

### **For Public Access:**

1. **HTTPS Required**
   - Ensure ARK runs on HTTPS
   - Use Let's Encrypt (free SSL)
   - Or Cloudflare SSL

2. **Authentication**
   - Enable authentication system (Enhancement #19)
   - Or limit access via WordPress user roles

3. **Rate Limiting**
   - Enable rate limiting (Enhancement #17)
   - Protect against abuse

4. **CORS Configuration**
   - Allow 1true.org domain
   - Update intelligent-backend.cjs:

```javascript
app.use(cors({
    origin: [
        'https://1true.org',
        'https://www.1true.org',
        'https://ark.1true.org'
    ],
    credentials: true
}));
```

---

## 📊 **Performance Optimization**

### **For WordPress Integration:**

1. **Use CDN**
   - Cloudflare (free tier)
   - Caches static assets
   - Improves global speed

2. **Lazy Loading**
```html
<iframe 
    src="YOUR_ARK_URL"
    loading="lazy"
    ...>
</iframe>
```

3. **Compression**
   - Enable Gzip on server
   - Minify CSS/JS

---

## 🎯 **Quick Start Checklist**

### **Option 1 (iFrame - 5 minutes):**
- [ ] Create WordPress page
- [ ] Add Custom HTML block
- [ ] Paste iFrame code with current sandbox URL
- [ ] Publish and test
- [ ] Plan permanent deployment

### **Option 2 (Subdomain - 30 minutes):**
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway
- [ ] Add DNS CNAME record
- [ ] Configure custom domain in Vercel
- [ ] Update WordPress menu

### **Option 3 (Plugin - 1 hour):**
- [ ] Create plugin file
- [ ] Upload to WordPress
- [ ] Activate plugin
- [ ] Configure settings
- [ ] Use shortcode in pages

---

## 📞 **Next Steps**

**I can help you with:**
1. Deploying ARK to Vercel/Railway
2. Creating the WordPress plugin
3. Setting up DNS records
4. Customizing the interface to match 1true.org
5. Adding authentication for WordPress users

**What would you like to do first?**

---

*Need help with any of these steps? Just ask!*
