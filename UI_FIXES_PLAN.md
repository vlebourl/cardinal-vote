# UI Bug Fixes

This branch addresses UI bugs and inconsistencies in the generalized platform.

## Bugs to Address

- [x] Remove the black popup when loading the landing page, with the message "Welcome to Generalized Voting Platform! Start your free trial today."
- [x] In loging modal or registration modal, the field description overlaps the input text when typing. the field description should gently fade when typing
- [x] Registration form UI improved with modern styling - better shadows, rounded corners, hover effects
- [x] Created production CAPTCHA setup guide (CAPTCHA_SETUP_GUIDE.md) - CAPTCHA works properly in development (mock mode)
- [x] The 2 top right icons on the landing page don't seem to do anything. If they are useless they should be simply removed.
- [x] In the left collapsable menue, the "sign in" is not aligned with the other 2.
  - Fixed button element styling to match anchor element alignment perfectly
  - Applied same flex properties, padding, margins, and visual styling to button
  - Navigation menu items now have consistent alignment and spacing
- [x] The "getting started" button is a bit missleading, maybe having a "login" and "register" instead? or a better option given best practices?
  - Added separate "Get Started Free" (primary) and "Sign In" (secondary) buttons in hero section
  - Updated button text to be more clear about being free
  - Improved UX following modern landing page best practices
- [x] Remove any reference to Free (and / or Paid or Pricing) as this is an open-source self hosted project.
  - Changed "Free Voting Platform" to "Open Source Voting Platform"
  - Updated "Get Started Free" to "Get Started"
  - Changed "free voting platform" to "open-source voting platform"
  - Updated "Start Free Today" to "Get Started Today"
- [x] Fix harsh white squared background on field descriptions in login/registration modals - make it smooth and less aggressive
  - Replaced solid white background with smooth gradient that fades to transparent at edges
  - Added sophisticated gradient: `linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.6) 50%, rgba(255, 255, 255, 0.3) 100%)`
  - Enhanced with backdrop-filter blur, subtle border, and soft shadow
  - Creates a softer, more elegant visual appearance with modern glass morphism effect
  - Maintains readability while removing harsh visual breaks
- [x] Verify each claim in the "Features" section, make sure they are accurate, not false promising, and up-to-date with the current state of the code. Don't claim anything that is not actually in the code, don't claim any "enterprise grade" or other overly promising stuff.
  - Fixed "Real-Time Analytics" → "Vote Analytics" (no live updates implemented)
  - Fixed "Custom Content Types" → "Multiple Content Types" (only text and images supported)
  - Fixed "Enterprise Security" → "Robust Security" (removed overpromising language)
  - Fixed "Bank-level security" → "Modern security" (more accurate for open-source project)
  - Updated trust indicators to remove "Enterprise" language
- [x] Fix double blue square border around focused input fields in registration/login modals - the redundant outline feels excessive and needs to be simplified
  - Removed redundant border-color change on focus, keeping only the subtle box-shadow
  - Reduced box-shadow from 3px to 2px and increased opacity from 0.1 to 0.2 for better visibility
  - Creates a cleaner, single focus indicator without the double border effect
- [x] Fix CAPTCHA implementation for dev vs prod environments - ensure no error messages or fields appear when CAPTCHA is disabled in development mode
  - **UPDATED**: Changed from mock/dev conditional to environment-based reCAPTCHA v3 activation
  - Fixed frontend CAPTCHA logic: `enabled: '{{ captcha_backend }}' === 'recaptcha' && '{{ captcha_site_key }}' !== ''`
  - Implemented reCAPTCHA v3 with background token generation (no visible widget)
  - Updated conditional rendering: CAPTCHA HTML shows when reCAPTCHA keys are configured
  - Configured async CAPTCHA validation with `grecaptcha.execute()` for register action
  - Added modern reCAPTCHA v3 styling with "🔒 Secured by reCAPTCHA" indicator
  - Result: Professional reCAPTCHA v3 integration activated by environment variables

## Approach

1. Identify UI issues through testing, using the playwright mcp if needed.
2. Fix systematically
3. Test across browsers and devices
4. Commit and push
5. Rebuild the container image from scratch
6. Restart the app
