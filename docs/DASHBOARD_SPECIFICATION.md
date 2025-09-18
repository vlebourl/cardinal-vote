# User Dashboard Specification - Cardinal Vote Platform

## Overview

This document defines the complete specification for the Cardinal Vote user dashboard, designed using Material Design 3 principles with modern UX patterns. The dashboard serves as the primary interface for vote creators to manage their votes and analyze results.

## Design Principles

### Material Design 3 Foundation

- **Modern visual hierarchy** with proper elevation, shadows, and surface treatments
- **Consistent typography scale** using Roboto font family
- **Dynamic color system** with primary (#0061a4), secondary, and surface colors
- **Responsive layout** that works seamlessly across desktop, tablet, and mobile
- **Smooth animations** and state transitions throughout the interface
- **Accessible design** meeting WCAG 2.1 AA standards

### User Experience Goals

- **Immediate value** - Users see their vote performance at a glance
- **Effortless navigation** - Clear information architecture with logical flow
- **Data-driven insights** - Visual analytics that help users understand their audience
- **Professional appearance** - Clean, modern interface that builds trust
- **Mobile-first approach** - Optimized for touch interactions and smaller screens

## Layout Architecture

### Top Navigation Bar (Fixed Header)

```
┌─[☰]─[Dashboard Title]────────────────────[+][👤]─┐
│                                                   │
```

- **Left**: Hamburger menu icon (☰) for drawer toggle
- **Center**: "Cardinal Vote Dashboard" title
- **Right**: Create vote button (+) and user profile menu (👤)
- **Material Design**: Elevated surface with shadow
- **Behavior**: Fixed position, visible on scroll
- **Z-index**: 100 (above content, below drawer)

### Navigation Drawer (Collapsible Sidebar)

**Default State**: CLOSED (completely hidden off-screen)
**Toggle Behavior**: Opens/closes via hamburger button with smooth slide animation

#### Drawer Header

```
┌─────────────────────────────┐
│ Welcome back!               │
│ John Doe                    │
│ john.doe@example.com        │
└─────────────────────────────┘
```

#### Navigation Items (Standard User)

```
┌─ 🏠 Dashboard              │
├─ 🗳️  My Votes               │
├─ 📊 Analytics              │
├─ ⚙️  Settings               │
├─────────────────────────────┤
└─ 🚪 Sign Out               │
```

#### Material Design Specifications

- **Width**: 280px (desktop), 260px (mobile)
- **Background**: Surface container (elevated)
- **Items**: 48px height with 16px padding
- **Icons**: 24px Material Icons
- **Typography**: Body Medium for labels
- **States**: Hover, active, and focus states
- **Z-index**: 200 (above content, below hamburger)

### Main Content Area

#### Content Structure

```
┌─[Welcome Hero Section]──────────────────┐
├─[Quick Stats Grid]─────────────────────┤
├─[Recent Activity Timeline]─────────────┤
├─[Active Votes Management]──────────────┤
└─[Vote Creation Interface]──────────────┘
```

## Section Specifications

### 1. Welcome Hero Section

**Purpose**: Immediate orientation and primary call-to-action

```
┌─────────────────────────────────────────────────────────────┐
│  🎯  Welcome to Your Voting Dashboard                       │
│                                                             │
│  Create engaging votes and gather valuable insights         │
│  from your community with our powerful platform.           │
│                                                             │
│  [📝 Create Your First Vote] [📚 View Tutorial]            │
└─────────────────────────────────────────────────────────────┘
```

**Visual Design**:

- **Background**: Primary container with subtle gradient
- **Typography**: Display Small for headline, Body Large for description
- **Buttons**: Filled primary, Outlined secondary
- **Spacing**: 32px padding, 16px between elements
- **Elevation**: Level 1 shadow

### 2. Quick Stats Grid

**Purpose**: At-a-glance performance metrics

```
┌─────────┬─────────┬─────────┬─────────┐
│  📊 42  │  🔴 12  │  👥 1.2K│  📈 28  │
│ Total   │ Active  │ Total   │ This    │
│ Votes   │ Votes   │Response │ Week    │
└─────────┴─────────┴─────────┴─────────┘
```

**Grid Specifications**:

- **Layout**: 4 columns (desktop), 2x2 grid (mobile)
- **Card Design**: Elevated surface with rounded corners (12px)
- **Content**: Large number (Title Large), descriptive label (Body Medium)
- **Icons**: 32px colored icons matching the metric type
- **Spacing**: 16px gaps between cards
- **Animation**: Number counter animation on load

### 3. Recent Activity Timeline

**Purpose**: Show recent vote activity and engagement

```
┌─ Recent Activity ─────────────────── Last 7 days ─┐
│                                                    │
│  🗳️  "Climate Policy Survey" received 47 votes     │
│      2 hours ago                                   │
│                                                    │
│  📊  "Product Feedback" closed with 156 responses  │
│      1 day ago                                     │
│                                                    │
│  ✨  "Team Building Ideas" went live               │
│      3 days ago                                    │
│                                                    │
│  [View All Activity →]                             │
└────────────────────────────────────────────────────┘
```

**Design Elements**:

- **Timeline Style**: Left-aligned with icon indicators
- **Typography**: Title Medium for actions, Body Small for timestamps
- **Colors**: Icons use semantic colors (success, warning, info)
- **Interaction**: Clickable items navigate to vote details
- **Empty State**: Encouraging illustration with getting started tips

### 4. Active Votes Management

**Purpose**: Quick actions on currently running votes

```
┌─ Active Votes ────────────────────── [View All →] ─┐
│                                                    │
│ ┌─ Climate Policy Survey ─────────── [⚙️][📊][⏸️] │
│ │ 47 responses • Started 3 days ago               │
│ │ ████████░░ 78% completion rate                  │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│ ┌─ Product Feedback ──────────────── [⚙️][📊][⏸️] │
│ │ 23 responses • Started 1 day ago                │
│ │ ███░░░░░░░ 32% completion rate                  │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│ [+ Create New Vote]                                │
└────────────────────────────────────────────────────┘
```

**Card Specifications**:

- **Layout**: Stacked cards with consistent spacing
- **Progress Bars**: Material Design linear indicators
- **Actions**: Icon buttons (Settings, Analytics, Pause/Resume)
- **States**: Clear visual states for active/paused/draft
- **Responsive**: Stack on mobile, side-by-side on desktop

### 5. Vote Creation Interface (Expandable)

**Purpose**: Quick vote creation without leaving dashboard

**Collapsed State**:

```
┌─ Quick Create ─────────────────────────────────────┐
│ [+ Create Vote] What would you like to ask?        │
└────────────────────────────────────────────────────┘
```

**Expanded State**:

```
┌─ Create New Vote ──────────────────────────────────┐
│                                                    │
│ Vote Title: [________________________]             │
│                                                    │
│ Description: [_____________________]               │
│              [_____________________]               │
│                                                    │
│ Options:                                           │
│ 1. [_____________________] [×]                     │
│ 2. [_____________________] [×]                     │
│ [+ Add Option]                                     │
│                                                    │
│ Access: ☐ Require login  ☐ Access code            │
│                                                    │
│ [Cancel] [Save as Draft] [Create & Launch]         │
└────────────────────────────────────────────────────┘
```

## Super Admin Dashboard Extensions

### Additional Navigation Items

The super admin sees additional items in the navigation drawer:

```
┌─ 🏠 Dashboard              │ ← Standard user items
├─ 🗳️  My Votes               │
├─ 📊 Analytics              │
├─ ⚙️  Settings               │
├─────────────────────────────┤
│ 🛡️  SUPER ADMIN            │ ← Visual separator
├─ 👥 User Management        │ ← Admin-only items
├─ 🗳️  All Votes              │
├─ 📊 System Analytics       │
├─ ⚙️  Platform Settings     │
├─ 🔧 System Health          │
├─────────────────────────────┤
└─ 🚪 Sign Out               │
```

### Admin-Specific Dashboard Sections

#### System Health Overview (Top Priority)

```
┌─ System Health ─────────────────────────────────────┐
│ 🟢 All Systems Operational                          │
│                                                     │
│ Active Users: 1,234    Database: Healthy           │
│ Total Votes: 5,678     Storage: 45% used           │
│ Response Rate: 89%     API Latency: 85ms           │
└─────────────────────────────────────────────────────┘
```

#### Platform Analytics Grid

```
┌──────────┬──────────┬──────────┬──────────┐
│ 👥 1,234 │ 🗳️ 5,678 │ 📊 89K   │ 🚀 +15% │
│ Active   │ Total    │ Total    │ Growth  │
│ Users    │ Votes    │ Response │ This    │
│          │          │          │ Month   │
└──────────┴──────────┴──────────┴──────────┘
```

#### Recent Platform Activity

```
┌─ Platform Activity ──────────────────────────────────┐
│                                                      │
│ 👤 new-user@example.com joined the platform          │
│    2 minutes ago                                     │
│                                                      │
│ 🗳️ "Company Survey" by admin@company.com exceeded     │
│    1000 responses                                    │
│    1 hour ago                                        │
│                                                      │
│ ⚠️  High database load detected and resolved          │
│    3 hours ago                                       │
│                                                      │
│ [View System Logs →]                                 │
└──────────────────────────────────────────────────────┘
```

#### User Management Quick Actions

```
┌─ User Management ────────────────────────────────────┐
│                                                      │
│ Recent Users:                                        │
│ • john.doe@example.com (2 votes, active)      [⚙️]  │
│ • mary.smith@company.com (1 vote, inactive)   [⚙️]  │
│ • admin@startup.com (15 votes, very active)   [⚙️]  │
│                                                      │
│ [View All Users] [Export User Data] [User Stats]    │
└──────────────────────────────────────────────────────┘
```

## Technical Implementation Requirements

### Responsive Breakpoints

- **Desktop**: 1200px+ (full layout)
- **Tablet**: 768px-1199px (adapted grid, collapsible sections)
- **Mobile**: <768px (stacked layout, drawer overlay)

### Performance Standards

- **Initial Load**: <2 seconds for dashboard content
- **Navigation**: <200ms for drawer animations
- **Data Updates**: Real-time or max 30-second refresh
- **Accessibility**: Full keyboard navigation, screen reader support

### State Management

- **Navigation State**: Drawer open/closed preference saved
- **Data Refresh**: Auto-refresh every 5 minutes for stats
- **Offline Support**: Cached data display when offline
- **Loading States**: Skeleton screens for all content areas

### Material Design Components

- **Cards**: Elevated surfaces with proper shadows
- **Buttons**: Filled, outlined, and text variants
- **Navigation**: Rail-style drawer with proper focus states
- **Data Display**: Data tables, charts, and progress indicators
- **Feedback**: Snackbars for actions, dialogs for confirmations

## Visual Design Standards

### Color Palette

- **Primary**: #0061a4 (Trust-building blue)
- **Primary Variant**: #004791
- **Secondary**: #6b5b95 (Complementary purple)
- **Surface**: #fdfcff (Clean white)
- **Error**: #ba1a1a (Clear error red)
- **Success**: #2e7d32 (Confirmation green)

### Typography Scale

- **Display Small**: 36px (Hero headlines)
- **Headline Large**: 32px (Section titles)
- **Headline Medium**: 28px (Subsection titles)
- **Title Large**: 22px (Card titles, important numbers)
- **Title Medium**: 16px (List items, labels)
- **Body Large**: 16px (Primary text)
- **Body Medium**: 14px (Secondary text)
- **Body Small**: 12px (Captions, timestamps)

### Spacing System

- **Base Unit**: 8px
- **Component Padding**: 16px (2 units)
- **Section Margins**: 24px (3 units)
- **Page Margins**: 32px (4 units)
- **Grid Gaps**: 16px between cards, 24px between sections

### Animation Specifications

- **Duration**: 200ms for micro-interactions, 300ms for major transitions
- **Easing**: Cubic-bezier(0.4, 0.0, 0.2, 1) for Material Motion
- **Drawer Animation**: Slide in/out with backdrop fade
- **Loading States**: Shimmer/skeleton animations
- **Hover Effects**: Subtle elevation and color changes

## Accessibility Requirements

### Keyboard Navigation

- **Tab Order**: Logical flow through all interactive elements
- **Focus Indicators**: Visible focus rings on all focusable elements
- **Skip Links**: Skip to main content option
- **Escape Key**: Closes modals and drawers

### Screen Reader Support

- **Semantic HTML**: Proper heading hierarchy and landmark roles
- **ARIA Labels**: Descriptive labels for interactive elements
- **Live Regions**: Announce dynamic content changes
- **Alt Text**: Descriptive text for all meaningful images

### Visual Accessibility

- **Color Contrast**: Minimum 4.5:1 for text, 3:1 for interactive elements
- **Text Scaling**: Readable at 200% zoom level
- **Motion Reduction**: Respect prefers-reduced-motion setting
- **Focus Management**: Clear visual focus indicators

This specification provides the complete blueprint for a modern, professional, and user-friendly dashboard that will replace the current broken implementation.
