# Production CAPTCHA Setup Guide

This guide explains how to configure production-ready CAPTCHA for the Generalized Voting Platform.

## Overview

The platform supports two CAPTCHA providers:

- **Google reCAPTCHA v2** (recommended for most use cases)
- **hCaptcha** (privacy-focused alternative)

Both providers are significantly more secure than the current mock CAPTCHA used in development.

## Why Use Production CAPTCHA?

- **Bot Prevention**: Stops automated registration and vote manipulation
- **Spam Protection**: Reduces fake accounts and malicious content
- **Rate Limiting**: Adds additional layer beyond IP-based limits
- **Compliance**: Meets security requirements for production applications

## Option 1: Google reCAPTCHA v2 (Recommended)

### 1. Get reCAPTCHA Keys

1. Visit [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Click "+" to create a new site
3. Fill out the form:
   - **Label**: "Generalized Voting Platform"
   - **reCAPTCHA type**: Select "reCAPTCHA v2" → "I'm not a robot" Checkbox
   - **Domains**: Add your production domains (e.g., `yourdomain.com`, `www.yourdomain.com`)
4. Accept the terms and click "Submit"
5. Copy the **Site Key** and **Secret Key**

### 2. Configure Environment Variables

Add these to your production environment (`.env` file or container environment):

```bash
# CAPTCHA Configuration
CAPTCHA_BACKEND=recaptcha
RECAPTCHA_SITE_KEY=your_site_key_here
RECAPTCHA_SECRET_KEY=your_secret_key_here
```

### 3. Update DNS/Domain Settings

- Ensure your production domain is properly configured
- reCAPTCHA validates against registered domains only

## Option 2: hCaptcha (Privacy-Focused)

### 1. Get hCaptcha Keys

1. Visit [hCaptcha Dashboard](https://dashboard.hcaptcha.com/)
2. Create an account or sign in
3. Go to "Sites" and click "New Site"
4. Configure:
   - **Name**: "Generalized Voting Platform"
   - **Hostnames**: Add your production domains
   - **Difficulty**: Choose appropriate level (Easy/Moderate/Difficult)
5. Save and copy the **Site Key** and **Secret Key**

### 2. Configure Environment Variables

```bash
# CAPTCHA Configuration
CAPTCHA_BACKEND=hcaptcha
HCAPTCHA_SITE_KEY=your_site_key_here
HCAPTCHA_SECRET_KEY=your_secret_key_here
```

## Implementation Status

✅ **Already Implemented**:

- Backend CAPTCHA service with provider abstraction
- Frontend JavaScript integration for both providers
- Template configuration for dynamic provider switching
- Proper error handling and user feedback
- Accessibility support (ARIA labels, screen reader friendly)

✅ **Code Locations**:

- Backend: `src/cardinal_vote/captcha_service.py`
- Frontend: `static/js/landing-material.js` (lines 470-590)
- Templates: `templates/landing_material.html` (CAPTCHA scripts)
- Configuration: `src/cardinal_vote/config.py`

## Testing Production CAPTCHA

### Local Testing

1. Set environment variables for your chosen provider
2. Restart the application
3. Test registration form - CAPTCHA widget should appear
4. Verify successful validation

### Production Deployment

1. Set environment variables in production environment
2. Deploy application
3. Test from different IPs/browsers
4. Monitor logs for CAPTCHA validation errors

## Security Considerations

### Rate Limiting

The application includes multiple protection layers:

- IP-based rate limiting (5 registrations per hour)
- CAPTCHA validation on each registration
- Content moderation flags limit

### CAPTCHA Bypass Protection

- CAPTCHA validation is server-side enforced
- Mock CAPTCHA only works in development (`localhost`)
- Production requires valid CAPTCHA response

### Privacy Compliance

- **reCAPTCHA**: Collects user data for Google services
- **hCaptcha**: More privacy-focused, minimal data collection
- Both comply with GDPR when properly configured

## Monitoring and Maintenance

### Metrics to Track

- CAPTCHA success/failure rates
- Registration completion rates
- Bot detection effectiveness
- User experience feedback

### Common Issues

1. **Domain Mismatch**: Ensure production domains match registered domains
2. **Key Rotation**: Update keys periodically for security
3. **Service Outages**: Monitor provider status pages
4. **False Positives**: Adjust difficulty if legitimate users struggle

### Logs to Monitor

```bash
# Check CAPTCHA validation logs
docker logs cardinal-vote-cardinal-vote-1 | grep -i captcha

# Monitor registration attempts
docker logs cardinal-vote-cardinal-vote-1 | grep -i "registration"
```

## Backup Plan

If primary CAPTCHA provider fails:

1. Switch to alternative provider via environment variables
2. Restart application
3. Monitor for restored functionality

## Cost Considerations

### Google reCAPTCHA

- **Free Tier**: 1 million assessments/month
- **Paid**: $1 per 1,000 assessments after free tier

### hCaptcha

- **Free Tier**: Unlimited for most websites
- **Enterprise**: Custom pricing for high volume

## Implementation Checklist

- [ ] Choose CAPTCHA provider (reCAPTCHA or hCaptcha)
- [ ] Register domain and get API keys
- [ ] Set production environment variables
- [ ] Deploy and test registration flow
- [ ] Monitor CAPTCHA validation rates
- [ ] Set up alerts for CAPTCHA failures
- [ ] Document keys in secure password manager
- [ ] Schedule periodic key rotation

## Quick Start Commands

```bash
# For reCAPTCHA
export CAPTCHA_BACKEND=recaptcha
export RECAPTCHA_SITE_KEY="your_site_key"
export RECAPTCHA_SECRET_KEY="your_secret_key"

# For hCaptcha
export CAPTCHA_BACKEND=hcaptcha
export HCAPTCHA_SITE_KEY="your_site_key"
export HCAPTCHA_SECRET_KEY="your_secret_key"

# Restart application
docker-compose up --build -d
```

The platform will automatically load the appropriate CAPTCHA widget and validate responses server-side. No code changes required!
