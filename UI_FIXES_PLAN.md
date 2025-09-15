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
- [x] Remove any reference to Free (and / or Paid or Pricing) as this is an open-source self hosted project.
  - Changed "Free Voting Platform" to "Open Source Voting Platform"
  - Updated "Get Started Free" to "Get Started"
  - Changed "free voting platform" to "open-source voting platform"
  - Updated "Start Free Today" to "Get Started Today"
- [x] Fix harsh white squared background on field descriptions in login/registration modals - make it smooth and less aggressive
  - Replaced solid white background with smooth gradient that fades to transparent at edges
  - Creates a softer, more elegant visual appearance
  - Maintains readability while removing harsh visual breaks

## Approach

- Identify UI issues through testing, using the playwright mcp if needed.
- Fix systematically
- Test across browsers and devices
- Commit and push
- Rebuild the container image from scratch
- Restart the app
