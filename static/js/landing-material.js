// Landing Page Material Design JavaScript

// Wait for DOM to be loaded
document.addEventListener('DOMContentLoaded', function () {
  // Navigation Drawer
  const navButton = document.querySelector('.md-top-app-bar-navigation-icon')
  const drawer = document.getElementById('navigationDrawer')
  const scrim = document.getElementById('navigationScrim')

  if (navButton && drawer && scrim) {
    navButton.addEventListener('click', () => {
      drawer.classList.toggle('md-navigation-drawer-open')
      scrim.classList.toggle('md-navigation-drawer-scrim-visible')
    })

    scrim.addEventListener('click', () => {
      drawer.classList.remove('md-navigation-drawer-open')
      scrim.classList.remove('md-navigation-drawer-scrim-visible')
    })
  }

  // Smooth scrolling for navigation links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute('href'))
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' })
        // Close drawer if open
        if (drawer && scrim) {
          drawer.classList.remove('md-navigation-drawer-open')
          scrim.classList.remove('md-navigation-drawer-scrim-visible')
        }
      }
    })
  })

  // Scroll to Top Button
  const scrollToTopBtn = document.getElementById('scrollToTop')

  if (scrollToTopBtn) {
    window.addEventListener('scroll', () => {
      if (window.pageYOffset > 300) {
        scrollToTopBtn.classList.add('visible')
      } else {
        scrollToTopBtn.classList.remove('visible')
      }
    })

    scrollToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    })
  }

  // Ripple Effect
  function createRipple(event) {
    const button = event.currentTarget
    const ripple = document.createElement('span')
    const diameter = Math.max(button.clientWidth, button.clientHeight)
    const radius = diameter / 2

    ripple.style.width = ripple.style.height = `${diameter}px`
    ripple.style.left = `${event.clientX - button.offsetLeft - radius}px`
    ripple.style.top = `${event.clientY - button.offsetTop - radius}px`
    ripple.classList.add('md-ripple-effect')

    button.appendChild(ripple)

    setTimeout(() => {
      ripple.remove()
    }, 600)
  }

  // Add ripple effect to all buttons
  document.querySelectorAll('.md-button, .md-fab, .md-card').forEach(element => {
    element.classList.add('md-ripple')
    element.addEventListener('click', createRipple)
  })

  // Snackbar functionality
  function showSnackbar(message, action = null) {
    const snackbar = document.getElementById('snackbar')
    const snackbarMessage = document.getElementById('snackbar-message')
    const snackbarAction = document.getElementById('snackbar-action')

    if (snackbar && snackbarMessage && snackbarAction) {
      snackbarMessage.textContent = message

      if (action) {
        snackbarAction.style.display = 'block'
        snackbarAction.onclick = action
      } else {
        snackbarAction.style.display = 'none'
      }

      snackbar.classList.add('md-snackbar-visible')

      setTimeout(() => {
        snackbar.classList.remove('md-snackbar-visible')
      }, 4000)
    }
  }

  // Dismiss snackbar
  const snackbarAction = document.getElementById('snackbar-action')
  if (snackbarAction) {
    snackbarAction.addEventListener('click', () => {
      const snackbar = document.getElementById('snackbar')
      if (snackbar) {
        snackbar.classList.remove('md-snackbar-visible')
      }
    })
  }

  // Show welcome message after page load
  window.addEventListener('load', () => {
    setTimeout(() => {
      showSnackbar('Welcome to Generalized Voting Platform! Start your free trial today.')
    }, 1000)
  })

  // Intersection Observer for animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-in-up')
        observer.unobserve(entry.target)
      }
    })
  }, observerOptions)

  // Observe feature cards and other elements
  document.querySelectorAll('.feature-card, .stat-item, .step-item').forEach(el => {
    observer.observe(el)
  })
})
