# ARK Chat WordPress Plugin

Integrate your ARK AI assistant into WordPress sites.

## Installation

1. **Download Plugin:**
   - Download the `ark-chat` folder
   - Zip the entire folder

2. **Upload to WordPress:**
   - Go to WordPress Admin → Plugins → Add New
   - Click "Upload Plugin"
   - Choose the `ark-chat.zip` file
   - Click "Install Now"
   - Activate the plugin

## Configuration

1. **Go to Settings → ARK Chat**

2. **Configure URLs:**
   - **Frontend URL:** Where your ARK frontend is hosted
     - Example: `https://ark.1true.org`
     - Or: `https://4173-sandbox.novita.ai`
   
   - **Backend API URL:** Where your ARK backend is hosted
     - Example: `https://ark-api.1true.org`
     - Or: `https://8000-sandbox.novita.ai`

3. **Optional Settings:**
   - Enable floating chat button
   - Choose button position (bottom-right, bottom-left, etc.)

## Usage

### Method 1: Shortcode (Recommended)

Add this shortcode to any page or post:

```
[ark_chat]
```

**With custom dimensions:**
```
[ark_chat width="100%" height="600px"]
```

### Method 2: Floating Button

Enable in settings to show a floating chat button on all pages.

### Method 3: Direct Link

Add a menu item pointing to your ARK URL.

## Features

- ✅ Easy shortcode integration
- ✅ Floating chat button
- ✅ Responsive design
- ✅ Mobile optimized
- ✅ Loading states
- ✅ Dark mode support
- ✅ Customizable positioning
- ✅ Beautiful animations

## Requirements

- WordPress 5.0 or higher
- PHP 7.2 or higher
- ARK system deployed and accessible via URL

## Support

For issues or questions:
- GitHub: https://github.com/Superman08091992/ark
- See `WORDPRESS_INTEGRATION_GUIDE.md` for detailed setup

## Changelog

### 1.0.0
- Initial release
- Shortcode support
- Floating button feature
- Admin settings page
- Responsive design
