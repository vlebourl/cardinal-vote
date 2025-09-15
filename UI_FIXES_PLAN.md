# UI Bug Fixes

This branch addresses UI bugs and inconsistencies in the generalized platform.

## Bugs to Address

- [x] Remove the black popup when loading the landing page, with the message "Welcome to Generalized Voting Platform! Start your free trial today."
- [x] In loging modal or registration modal, the field description overlaps the input text when typing. the field description should gently fade when typing
- [x] Registration form UI improved with modern styling - better shadows, rounded corners, hover effects
- [x] Created production CAPTCHA setup guide (CAPTCHA_SETUP_GUIDE.md) - CAPTCHA works properly in development (mock mode)
- [x] The 2 top right icons on the landing page don't seem to do anything. If they are useless they should be simply removed.
- [x] In the left collapsable menue, the "sign in" is not aligned with the other 2.
- [x] The "getting started" button is a bit missleading, maybe having a "login" and "register" instead? or a better option given best practices?
  - Added separate "Get Started Free" (primary) and "Sign In" (secondary) buttons in hero section
  - Updated button text to be more clear about being free
  - Improved UX following modern landing page best practices

## Approach

- Identify UI issues through testing, using the playwright mcp if needed.
- Fix systematically
- Test across browsers and devices
- Rebuild the container image from scratch
- Restart the app
