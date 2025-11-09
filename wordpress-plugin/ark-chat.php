<?php
/**
 * Plugin Name: ARK Chat Assistant
 * Plugin URI: https://github.com/Superman08091992/ark
 * Description: Integrates ARK AI assistant into WordPress for 1true.org
 * Version: 1.0.0
 * Author: Superman08091992
 * Author URI: https://1true.org
 * License: MIT
 * Text Domain: ark-chat
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Main ARK Chat Plugin Class
 */
class ARK_Chat_Plugin {
    
    private $version = '1.0.0';
    
    public function __construct() {
        // Initialize plugin
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
        add_shortcode('ark_chat', array($this, 'ark_chat_shortcode'));
        add_action('wp_footer', array($this, 'floating_chat_button'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_styles'));
    }
    
    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_options_page(
            'ARK Chat Settings',
            'ARK Chat',
            'manage_options',
            'ark-chat-settings',
            array($this, 'settings_page')
        );
    }
    
    /**
     * Register plugin settings
     */
    public function register_settings() {
        register_setting('ark_chat_settings', 'ark_chat_url');
        register_setting('ark_chat_settings', 'ark_chat_enable_floating');
        register_setting('ark_chat_settings', 'ark_chat_floating_position');
        register_setting('ark_chat_settings', 'ark_chat_api_url');
    }
    
    /**
     * Settings page HTML
     */
    public function settings_page() {
        if (!current_user_can('manage_options')) {
            return;
        }
        
        // Save settings
        if (isset($_POST['submit'])) {
            update_option('ark_chat_url', sanitize_text_field($_POST['ark_chat_url']));
            update_option('ark_chat_api_url', sanitize_text_field($_POST['ark_chat_api_url']));
            update_option('ark_chat_enable_floating', isset($_POST['ark_chat_enable_floating']) ? '1' : '0');
            update_option('ark_chat_floating_position', sanitize_text_field($_POST['ark_chat_floating_position']));
            echo '<div class="updated"><p><strong>Settings saved successfully!</strong></p></div>';
        }
        
        $ark_url = get_option('ark_chat_url', '');
        $ark_api_url = get_option('ark_chat_api_url', '');
        $enable_floating = get_option('ark_chat_enable_floating', '0');
        $floating_position = get_option('ark_chat_floating_position', 'bottom-right');
        
        ?>
        <div class="wrap">
            <h1>🌌 ARK Chat Assistant Settings</h1>
            
            <form method="post" action="">
                <table class="form-table">
                    <tr valign="top">
                        <th scope="row">Frontend URL</th>
                        <td>
                            <input type="url" 
                                   name="ark_chat_url" 
                                   value="<?php echo esc_attr($ark_url); ?>"
                                   class="regular-text"
                                   placeholder="https://ark.1true.org">
                            <p class="description">The URL where your ARK frontend is hosted</p>
                        </td>
                    </tr>
                    
                    <tr valign="top">
                        <th scope="row">Backend API URL</th>
                        <td>
                            <input type="url" 
                                   name="ark_chat_api_url" 
                                   value="<?php echo esc_attr($ark_api_url); ?>"
                                   class="regular-text"
                                   placeholder="https://ark-backend.1true.org">
                            <p class="description">The URL where your ARK backend API is hosted</p>
                        </td>
                    </tr>
                    
                    <tr valign="top">
                        <th scope="row">Floating Chat Button</th>
                        <td>
                            <label>
                                <input type="checkbox" 
                                       name="ark_chat_enable_floating" 
                                       value="1"
                                       <?php checked($enable_floating, '1'); ?>>
                                Enable floating chat button on all pages
                            </label>
                        </td>
                    </tr>
                    
                    <tr valign="top">
                        <th scope="row">Button Position</th>
                        <td>
                            <select name="ark_chat_floating_position">
                                <option value="bottom-right" <?php selected($floating_position, 'bottom-right'); ?>>Bottom Right</option>
                                <option value="bottom-left" <?php selected($floating_position, 'bottom-left'); ?>>Bottom Left</option>
                                <option value="top-right" <?php selected($floating_position, 'top-right'); ?>>Top Right</option>
                                <option value="top-left" <?php selected($floating_position, 'top-left'); ?>>Top Left</option>
                            </select>
                        </td>
                    </tr>
                </table>
                
                <?php submit_button(); ?>
            </form>
            
            <hr>
            
            <h2>📖 Usage Instructions</h2>
            
            <h3>Method 1: Shortcode</h3>
            <p>Add this shortcode to any page or post to embed the full ARK chat interface:</p>
            <code>[ark_chat]</code>
            
            <p>With custom dimensions:</p>
            <code>[ark_chat width="100%" height="600px"]</code>
            
            <h3>Method 2: Floating Button</h3>
            <p>Enable the floating button above to show a chat button on all pages.</p>
            
            <h3>Method 3: Direct Link</h3>
            <p>Add a link to your menu pointing to:</p>
            <code><?php echo esc_html($ark_url); ?></code>
            
            <hr>
            
            <h2>🚀 Deployment Options</h2>
            <ol>
                <li><strong>Vercel</strong> (Recommended for Frontend) - Free, fast, automatic SSL</li>
                <li><strong>Railway</strong> (Recommended for Backend) - Free tier, easy deployment</li>
                <li><strong>Subdomain</strong> - Use ark.1true.org for professional appearance</li>
            </ol>
            
            <p>See <code>WORDPRESS_INTEGRATION_GUIDE.md</code> in the ARK repository for detailed instructions.</p>
        </div>
        <?php
    }
    
    /**
     * Shortcode for embedding ARK chat
     */
    public function ark_chat_shortcode($atts) {
        $atts = shortcode_atts(array(
            'height' => '800px',
            'width' => '100%',
        ), $atts);
        
        $ark_url = get_option('ark_chat_url', '');
        
        if (empty($ark_url)) {
            return '<p style="color: red;">⚠️ ARK Chat URL not configured. Please configure in Settings → ARK Chat</p>';
        }
        
        ob_start();
        ?>
        <div class="ark-chat-embed-container">
            <div class="ark-loading" id="ark-loading-<?php echo uniqid(); ?>">
                <div class="ark-spinner"></div>
                <p>Loading ARK System...</p>
            </div>
            
            <iframe 
                class="ark-chat-iframe"
                src="<?php echo esc_url($ark_url); ?>"
                width="<?php echo esc_attr($atts['width']); ?>"
                height="<?php echo esc_attr($atts['height']); ?>"
                frameborder="0"
                allow="microphone; camera; geolocation"
                onload="this.previousElementSibling.style.display='none'">
            </iframe>
        </div>
        <?php
        return ob_get_clean();
    }
    
    /**
     * Floating chat button
     */
    public function floating_chat_button() {
        $enable_floating = get_option('ark_chat_enable_floating', '0');
        
        if ($enable_floating !== '1') {
            return;
        }
        
        $ark_url = get_option('ark_chat_url', '');
        if (empty($ark_url)) {
            return;
        }
        
        $position = get_option('ark_chat_floating_position', 'bottom-right');
        
        // Calculate position styles
        $position_styles = array(
            'bottom-right' => 'bottom: 20px; right: 20px;',
            'bottom-left' => 'bottom: 20px; left: 20px;',
            'top-right' => 'top: 20px; right: 20px;',
            'top-left' => 'top: 20px; left: 20px;'
        );
        
        $style = isset($position_styles[$position]) ? $position_styles[$position] : $position_styles['bottom-right'];
        
        ?>
        <div id="ark-floating-chat" style="position: fixed; <?php echo $style; ?> z-index: 99999;">
            <a href="<?php echo esc_url($ark_url); ?>" 
               target="_blank"
               rel="noopener noreferrer"
               class="ark-floating-button"
               title="Open ARK Chat Assistant">
                <span class="ark-button-icon">🌌</span>
                <span class="ark-button-text">Chat</span>
            </a>
        </div>
        <?php
    }
    
    /**
     * Enqueue plugin styles
     */
    public function enqueue_styles() {
        wp_enqueue_style('ark-chat-styles', plugins_url('assets/ark-chat.css', __FILE__), array(), $this->version);
    }
}

// Initialize plugin
new ARK_Chat_Plugin();
