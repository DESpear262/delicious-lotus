# Front-End Style & Theming Guide
## Overview
This guide defines a modern, slick UI theme with light cyberpunk influences for the AI Video Generation Pipeline frontend.

## Core Aesthetic
- Clean minimalism with neon accents.
- Light cyberpunk: holographic hues, subtle scanlines, soft glows.
- High contrast UI with dark steel backgrounds and iridescent UI elements.

## Color Palette
### Primary Colors
- **Dark Background**: `#0A0F14` (deep charcoal with blue undertone)
- **Panel Charcoal**: `#111820`
- **Off-White Text**: `#E6F1FF`

### Accent Colors (Cyberpunk Neon)
- **Neon Blue**: `#00E5FF`
- **Holographic Purple**: `#BD59FF`
- **Soft Teal**: `#43FFC9`
- **Neon Orange**: `#FF8A3D`
- **Signal Green**: `#6CFF7F`

### Gradient Accents
Use sparingly for emphasis:
- **Blue → Purple**: `linear-gradient(90deg, #00E5FF, #BD59FF)`
- **Teal → Blue**: `linear-gradient(90deg, #43FFC9, #00E5FF)`

## Typography
### Font Families
- **Headings:** Inter, Eurostile, or Orbitron
- **Body Text:** Inter, Roboto
- **Monospace:** JetBrains Mono (for logs, code-like UI)

### Rules
- Wide letter spacing for headings
- High contrast, but avoid pure white
- Use neon accents only for emphasis

## UI Components

### Buttons
#### Primary Button
- Background: Neon Blue
- Text: Dark Background
- Hover: Glow (`0 0 12px #00E5FF`)
- Border-radius: 6px

#### Secondary Button
- Border: 1px solid Neon Blue
- Text: Neon Blue
- Hover: subtle panel glow

### Cards
- Glassmorphism style:
  - Background: `rgba(20, 25, 35, 0.45)`
  - Border: 1px solid `rgba(0, 229, 255, 0.2)`
  - Backdrop blur: `12px`
- Hover: holographic shimmer animation

### Panels / Containers
- Subtle scanline pattern overlay (2–3% opacity)
- Neon border bottom for section headers

## Layout Guidance
- Use a dashboard-style three-column grid where appropriate
- Left sidebar: holographic blur panel
- Right sidebar: job activity, notifications
- Center content: prompt inputs, scene preview panels

## Animations (Subtle by default)
- Hover glows with low-frequency pulsing
- Scene preview transitions:
  - Fade + slight scale-up (1.02)
- Neon borders animate:
  - 4-second slow glow loop

## Imagery & Visual Language
- Thumbnails use filmic contrast with neon overlays
- Optional VHS grain at 2–5% opacity
- Icons in neon blue with thin-line style

## Iconography
- Use Tabler Icons or custom neon-outline icons
- Maintain consistent stroke width
- Active-state icons animate with a slight glow pulse

## Responsive Design
- Mobile-first grid scaling
- Sidebar collapses into neon-icon-only rail
- Prompt input expands to full width on small screens

## Accessibility Considerations
- Maintain 4.5:1 contrast ratio (neon must not overpower readability)
- Provide “reduced animation” mode
- Avoid pure red/green for status indicators (use teal/orange instead)

## Component Examples
### CTA Panel Example
- Card with holographic border
- Neon gradient headline
- Soft glow around action buttons

### Progress Timeline UI
- Neon ticks and markers
- Subtle animated pulse on active step

## General Do’s and Don’ts
### Do
- Use neon only for emphasis
- Keep 80–90% of screen dark/neutral
- Use frosted-glass cards for layered depth

### Don’t
- Overuse glow effects
- Use pure white or pure black
- Mix too many neon colors in one component

---
This theming guide supports a sleek, modern, light-cyberpunk look aligned with the project PRD while preserving usability, clarity, and professional polish.
