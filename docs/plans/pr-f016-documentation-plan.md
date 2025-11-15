# PR-F016: User Documentation Implementation Plan

## Overview
Create comprehensive user-facing documentation including user guide, FAQ, and prompt engineering best practices, along with in-app help components.

**Estimated Time:** 2 hours  
**Dependencies:** None (parallel work)  
**Priority:** MEDIUM - Can be done in parallel with other PRs

## Goals
- Provide clear, non-technical documentation for end users
- Help users get started quickly with the platform
- Teach effective prompt writing techniques
- Answer common questions proactively
- Enable in-app contextual help

---

## Files to Create

### 1. `/home/user/delicious-lotus/docs/user-guide.md`
**Purpose:** Comprehensive user guide for the platform

**Content Structure:**
```markdown
# AI Video Generation Platform - User Guide

## Table of Contents
1. Introduction
2. Getting Started
3. Creating Your First Ad Creative
4. Understanding the Generation Process
5. Using Brand Assets
6. Configuring Video Parameters
7. Downloading and Sharing Videos
8. Generation History
9. Troubleshooting

## 1. Introduction

Welcome to the AI Video Generation Platform! This tool helps you create professional video advertisements in minutes using AI.

**What you can create:**
- Ad Creative videos (15-60 seconds)
- Product showcase videos
- Service promotion videos
- Event announcement videos

**What you'll need:**
- A clear description of your video concept
- (Optional) Brand assets like logos and colors
- A few minutes for AI generation

## 2. Getting Started

### Accessing the Platform
1. Navigate to the platform URL
2. The home page shows available pipeline options
3. Select "Ad Creative" to begin

### Platform Overview
- **Home:** Start a new video generation
- **History:** View all your previous generations

## 3. Creating Your First Ad Creative

### Step 1: Write Your Prompt
A prompt is a description of the video you want to create.

**Example prompts:**
- "Create a 30-second ad for a luxury watch brand showcasing elegance and precision with gold accents"
- "Product showcase for eco-friendly water bottles, highlighting sustainability and modern design"
- "Energetic ad for a fitness app with motivational scenes and vibrant colors"

**Tips:**
- Be specific about your product/service
- Describe the mood and style you want
- Mention key visual elements
- Include your target audience if relevant
- Length: 500-2000 characters

### Step 2: Configure Brand Settings
Make your video match your brand identity:

**Brand Name:**
- Enter your company or product name
- This may appear in the video

**Logo Upload:**
- Supported formats: JPEG, PNG
- Maximum size: 50MB
- Recommended: Square logo, at least 512x512 pixels
- Transparent background (PNG) works best

**Brand Colors:**
- Primary color: Main brand color
- Secondary color: Accent color
- Use hex codes (e.g., #FF5733)

**Call-to-Action (CTA):**
- Toggle on to include a CTA
- Example CTAs: "Shop Now", "Learn More", "Sign Up Today"
- Keep it short (2-4 words)

### Step 3: Set Video Parameters

**Duration:**
- 15 seconds: Quick, punchy ads
- 30 seconds: Standard ad length
- 45 seconds: Detailed product showcase
- 60 seconds: Full story or multiple products

**Aspect Ratio:**
- 16:9 (Landscape): YouTube, website
- 9:16 (Portrait): Instagram Stories, TikTok
- 1:1 (Square): Instagram Feed, Facebook

**Style:**
- Professional: Corporate, polished
- Casual: Friendly, approachable
- Modern: Sleek, minimalist
- Dynamic: Energetic, fast-paced

**Music Style:**
- Corporate: Professional, upbeat
- Upbeat: Energetic, positive
- Cinematic: Epic, dramatic
- Ambient: Calm, subtle

### Step 4: Review and Submit
- Review all your settings
- Check estimated generation time (typically 3-5 minutes)
- Click "Generate Video"
- You'll be redirected to the progress page

## 4. Understanding the Generation Process

After submitting, your video goes through several stages:

**1. Input Validation (< 1 minute)**
- System validates your prompt and settings
- Checks uploaded assets

**2. Content Planning (1-2 minutes)**
- AI analyzes your prompt
- Plans scenes and transitions
- Generates shot list

**3. Asset Generation (2-3 minutes)**
- AI creates individual video clips
- Generates visuals based on your prompt
- You'll see clips appear as they complete

**4. Video Composition (1 minute)**
- Clips are stitched together
- Music is added
- Transitions are applied
- Logo and CTA are overlaid

**5. Final Rendering (< 1 minute)**
- Final video is encoded
- Thumbnail is generated
- Video is ready for download

**Total Time:** 3-7 minutes (depending on duration and complexity)

**Progress Indicators:**
- Overall progress bar
- Step-by-step status
- Individual clip previews
- Estimated time remaining

**During Generation:**
- Keep the browser tab open
- You can minimize the window
- Real-time updates via WebSocket
- Cancel anytime if needed

## 5. Using Brand Assets

### Logo Guidelines

**Best Practices:**
- Use a high-resolution logo (at least 512x512)
- PNG format with transparent background preferred
- Simple logos work better than complex ones
- Ensure good contrast with video backgrounds

**Positioning:**
- Logo typically appears in corner
- Visible throughout video or at end
- Sized appropriately for aspect ratio

### Color Usage

**How Colors Are Used:**
- Background elements
- Text overlays
- Transitions
- Accent highlights

**Tips:**
- Choose contrasting colors for visibility
- Stick to your brand guidelines
- Test with different aspect ratios

## 6. Configuring Video Parameters

### Choosing Duration

**15 seconds:**
- Best for: Social media ads, quick announcements
- Attention span: Maximum impact
- Cost: Lower

**30 seconds:**
- Best for: Standard advertising
- Attention span: Good balance
- Cost: Medium
- Most popular choice

**45 seconds:**
- Best for: Product demonstrations
- Attention span: Detailed storytelling
- Cost: Medium-high

**60 seconds:**
- Best for: Brand stories, multiple products
- Attention span: Full narrative
- Cost: Higher

### Choosing Aspect Ratio

**16:9 (Landscape):**
- Platforms: YouTube, website embeds, presentations
- Best for: Desktop viewing, detailed content
- Most cinematic format

**9:16 (Portrait):**
- Platforms: Instagram/Facebook Stories, TikTok, Snapchat
- Best for: Mobile-first content
- Maximum screen real estate on phones

**1:1 (Square):**
- Platforms: Instagram Feed, Facebook Feed, LinkedIn
- Best for: Feed posts, versatile viewing
- Works on both mobile and desktop

**Pro Tip:** Create multiple versions with different aspect ratios for different platforms!

## 7. Downloading and Sharing Videos

### Downloading Your Video

**After generation completes:**
1. Click the "Download" button
2. Choose save location
3. Video downloads as MP4 file
4. High quality (1080p, H.264 codec)

**File Details:**
- Format: MP4 (universally compatible)
- Codec: H.264
- Resolution: 1080p (1920x1080 for 16:9)
- File size: Typically 5-20MB depending on duration

### Video Player Features

**Playback Controls:**
- Play/Pause
- Seek timeline
- Volume control
- Playback speed (0.5x to 2x)
- Fullscreen mode

**Keyboard Shortcuts:**
- Spacebar: Play/Pause
- ← →: Seek backward/forward 5 seconds
- ↑ ↓: Volume control
- F: Fullscreen
- M: Mute

### Sharing Options

**Direct Download:**
- Download to your device
- Upload to your preferred platforms

**Future Features:**
- Direct social media sharing
- Shareable links
- Embed codes

## 8. Generation History

### Viewing Your History

**Access:**
- Click "History" in navigation
- See all your previous generations

**Information Displayed:**
- Thumbnail preview
- Generation ID
- Creation date and time
- Status (completed, processing, failed)
- Duration
- Quick actions

**Statuses:**
- ✅ Completed: Ready to view/download
- ⏳ Processing: Currently generating
- 🔄 Composing: Stitching clips together
- ⏸ Queued: Waiting to start
- ❌ Failed: Generation error
- 🚫 Cancelled: User cancelled

### Managing History

**Actions:**
- View: Preview the video
- Download: Download the file
- Re-run: Create similar video with same settings
- Delete: Remove from history

**Filtering:**
- Filter by status
- Filter by date range
- Search by prompt text

**Sorting:**
- Newest first (default)
- Oldest first
- By duration

## 9. Troubleshooting

### Common Issues

**Issue: "Failed to load video"**
- Solution: Refresh the page, click retry
- Check your internet connection
- Try downloading again

**Issue: "Generation failed"**
- Reason: AI service error, invalid prompt
- Solution: Check error message, try again
- Modify prompt if too complex

**Issue: "Upload failed"**
- Check file type (JPEG/PNG only)
- Check file size (max 50MB)
- Ensure image is not corrupted

**Issue: "Video quality is not as expected"**
- AI generation is variable
- Try regenerating with modified prompt
- Be more specific in your description

**Issue: "Generation taking too long"**
- Normal time: 3-7 minutes
- If > 10 minutes, refresh page
- Check status in history page

**Issue: "Logo not visible in video"**
- Ensure logo has good contrast
- Try PNG with transparent background
- Check logo file is not corrupted

### Getting Help

**In-App Help:**
- Hover over ? icons for tooltips
- Click help links for detailed guides

**Support:**
- Check FAQ section
- Review prompt best practices
- Contact support (future feature)

### Best Practices for Success

**Do:**
✅ Write detailed, specific prompts
✅ Use high-quality brand assets
✅ Choose appropriate duration for your message
✅ Test different prompts and settings
✅ Review before downloading

**Don't:**
❌ Use copyrighted content in prompts
❌ Upload low-quality logos
❌ Make prompts too vague
❌ Expect identical results every time
❌ Close browser during generation

---

## Tips for Great Videos

1. **Be Specific:** The more detail in your prompt, the better
2. **Know Your Audience:** Describe who you're targeting
3. **Emphasize Key Points:** Highlight what matters most
4. **Keep It Simple:** Clear message beats complex ideas
5. **Test Variations:** Try different prompts for same concept
6. **Use Brand Assets:** Logos and colors increase recognition
7. **Choose Right Duration:** Match content to time available
8. **Select Appropriate Aspect:** Think about where it will be shown
9. **Review Carefully:** Watch the whole video before using
10. **Iterate:** Regenerate with tweaks until satisfied

---

## Glossary

**AI (Artificial Intelligence):** Computer system that can perform tasks typically requiring human intelligence

**Aspect Ratio:** The proportional relationship between width and height (e.g., 16:9)

**CTA (Call-to-Action):** Text prompting viewers to take action (e.g., "Shop Now")

**Generation:** The process of creating a video from your prompt

**Hex Code:** Six-character code representing a color (e.g., #FF5733)

**MP4:** Video file format compatible with most devices and platforms

**Prompt:** Text description of the video you want to create

**Render:** Convert video components into final video file

**Thumbnail:** Small preview image of the video

**WebSocket:** Technology enabling real-time updates during generation

---

*Last updated: November 2025*
```

---

### 2. `/home/user/delicious-lotus/docs/faq.md`
**Purpose:** Frequently asked questions

**Content:**
```markdown
# Frequently Asked Questions (FAQ)

## General Questions

### What is this platform?
The AI Video Generation Platform uses artificial intelligence to create professional video advertisements from text descriptions. You provide a prompt and settings, and our AI generates a complete video with scenes, transitions, and music.

### Do I need video editing experience?
No! The platform is designed for anyone to use. Just describe what you want, configure some settings, and the AI does the rest.

### Is the platform free?
Pricing information will be added here. MVP version may have usage limits.

### What video types can I create?
Currently:
- **Ad Creative** (15-60 seconds): Product ads, service promotions, event announcements

Coming soon:
- **Music Video** (60-180 seconds): Music videos with audio synchronization

## Video Generation

### How long does video generation take?
Typical generation times:
- 15-second video: ~3 minutes
- 30-second video: ~4 minutes
- 45-second video: ~5 minutes
- 60-second video: ~7 minutes

Times may vary based on complexity and server load.

### What is the maximum video duration?
**Ad Creative:** 15-60 seconds
**Music Video (coming soon):** 60-180 seconds

### Can I cancel a generation in progress?
Yes! Click the "Cancel" button on the progress page. The generation will stop, and you won't be charged (if applicable).

### What happens if generation fails?
You'll see an error message explaining what went wrong. Common reasons:
- Invalid or inappropriate prompt
- AI service temporary outage
- File upload issues

You can try again immediately. Failed generations don't count against quotas.

### Can I regenerate a video with the same settings?
Yes! From the history page, click "Re-run" on any completed generation to load the same settings into a new generation form.

### Will I get the same video if I use the same prompt twice?
No. AI generation is creative and variable. Each generation will be unique, even with identical settings. This allows for variation and creativity.

## Prompts and Content

### How do I write a good prompt?
See our [Prompt Best Practices](./prompt-best-practices.md) guide for detailed tips. In short:
- Be specific and detailed
- Describe visuals, mood, and style
- Mention key product/service features
- Specify target audience
- Use 500-2000 characters

### What language should I use in prompts?
English is currently supported. Other languages coming soon.

### Can I use copyrighted content in my prompts?
No. Don't reference copyrighted characters, brands, or content you don't own. Stick to original descriptions.

### What content is not allowed?
Prohibited content includes:
- Violence or gore
- Adult/sexual content
- Hate speech or discrimination
- Illegal activities
- Copyrighted material
- Misleading or fraudulent claims

### Can I include multiple products in one video?
Yes, but keep in mind:
- 15-30 seconds: Single product works best
- 45-60 seconds: Can feature 2-3 products
- Longer videos allow more complex narratives

## Technical Questions

### What aspect ratios are supported?
- **16:9 (Landscape):** 1920x1080 - YouTube, websites
- **9:16 (Portrait):** 1080x1920 - Instagram Stories, TikTok
- **1:1 (Square):** 1080x1080 - Instagram/Facebook Feed

### What video format do I get?
- Format: MP4
- Codec: H.264
- Resolution: 1080p (Full HD)
- Frame rate: 30fps
- Audio: AAC, stereo

This format works on all major platforms and devices.

### What file formats can I upload for logos?
- JPEG (.jpg, .jpeg)
- PNG (.png) - recommended for transparent backgrounds

Maximum file size: 50MB

### What are the image dimension requirements?
**Minimum:** 512x512 pixels
**Maximum:** 4096x4096 pixels
**Recommended:** 1024x1024 or larger, square aspect ratio

### Can I upload my own music?
Currently: No (AI generates background music)
**Coming soon:** Music Video pipeline will support custom audio uploads

### Do I need an account to use the platform?
MVP version may not require accounts. Future versions will have user accounts for saving history and managing projects.

### What browsers are supported?
**Fully supported:**
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)

**Mobile:**
- iOS Safari
- Chrome Android

### Does it work on mobile devices?
Yes! The platform is responsive and works on tablets and phones. However, desktop is recommended for best experience, especially for uploading files.

### Do I need to keep the browser open during generation?
Yes, keep the browser tab open while generating. You can minimize the window, but don't close the tab. Progress updates are delivered in real-time via WebSocket connection.

If you accidentally close the tab, navigate back to the History page to check status.

## Brand Assets

### Why should I upload a logo?
Your logo helps:
- Build brand recognition
- Make video look professional
- Ensure consistent branding
- Credit your brand visually

### Where will my logo appear?
Typically in the corner of the video, either throughout or in the final frames. The AI determines optimal placement based on video content.

### My logo isn't showing up. What's wrong?
**Possible issues:**
- File too small (< 512x512)
- File corrupted
- Poor contrast with video
- File format issue

**Solutions:**
- Use larger image (1024x1024+)
- Use PNG with transparent background
- Ensure logo has clear edges and contrast
- Re-upload the file

### How are brand colors used?
Brand colors influence:
- Background elements
- Text overlays
- Transition effects
- Accent highlights
- Overall color palette

### Can I change settings after starting generation?
No. Once you click "Generate Video," settings are locked. If you want different settings, cancel and start a new generation.

## Video Output

### How do I download my video?
1. Wait for generation to complete
2. You'll be redirected to the preview page
3. Click the "Download" button
4. Choose save location
5. Video downloads as MP4 file

### Can I edit the generated video?
The platform doesn't include video editing tools. However, you can:
- Download the MP4 file
- Import into any video editor (Adobe Premiere, Final Cut, DaVinci Resolve, etc.)
- Edit as needed

Future feature: AI-assisted editing with natural language commands.

### Can I get the video in different resolutions?
Currently: Only 1080p
**Coming soon:** 4K option, 720p option for smaller files

### How long are videos stored?
Video retention policy:
- **MVP:** 30 days minimum
- **Future:** Permanent storage for account holders

Download your videos for local backup!

### Can I share videos directly to social media?
Currently: No, must download first
**Coming soon:** Direct sharing to Instagram, Facebook, YouTube, TikTok

### What's the typical file size?
Depends on duration:
- 15 seconds: ~5-8 MB
- 30 seconds: ~10-15 MB
- 45 seconds: ~15-20 MB
- 60 seconds: ~20-25 MB

Sizes vary based on content complexity and motion.

## Troubleshooting

### Video won't play in the preview
**Try:**
1. Refresh the page
2. Click the retry button
3. Wait a moment for buffering
4. Check internet connection
5. Try different browser

### Download is failing
**Try:**
1. Check available disk space
2. Try different browser
3. Disable browser extensions
4. Check antivirus/firewall settings
5. Use "Save As" instead of default download

### Video looks blurry or low quality
**Possible causes:**
- Internet buffering (not actual video quality)
- Browser compression during preview
- Display scaling

**Solution:** Download the video and play locally for true quality

### Error: "Generation failed"
**What to do:**
1. Read the error message
2. Check your prompt and settings
3. Verify uploaded files are valid
4. Try again after a moment
5. If persists, contact support

### WebSocket connection failed
**What it means:** Real-time updates unavailable
**What happens:** Automatic fallback to polling (updates every 5 seconds instead of instant)
**Your action:** None required, generation continues normally

## Account and History

### Where can I see my previous videos?
Click "History" in the navigation menu to see all generations.

### Can I delete old generations?
Yes, click the delete button on any generation in the history page. This is permanent and cannot be undone.

### How many videos can I create?
MVP version may have limits. Future versions will have tiered plans with different quotas.

### Can I export my generation history?
Not currently available. Future feature: Export history as CSV/JSON.

## Pricing and Limits

### How much does each video cost?
Pricing structure will be announced. Possible models:
- Free tier with limits
- Pay-per-generation
- Monthly subscription
- Enterprise plans

### Are there usage limits?
MVP may have rate limits:
- X generations per hour
- Y generations per day

Exact limits to be determined.

### Do failed generations count against my quota?
No. Only successful completions count.

### Can I get a refund if I don't like the video?
Refund policy to be determined. Consider regenerating with modified prompt first.

## Future Features

### What features are coming next?
**Planned features:**
- Music Video pipeline with custom audio
- Advanced timeline editing
- AI-assisted video editing with natural language
- Direct social media integration
- Template library
- Batch generation
- Team collaboration
- Analytics and performance tracking

### When will Music Video be available?
Music Video pipeline is planned for post-MVP (8-14 days after MVP launch).

### Can I request a feature?
Yes! Feature request system coming soon. We value user feedback.

### Will there be an API?
Enterprise API is planned for future release.

---

## Still Have Questions?

**Check these resources:**
- [User Guide](./user-guide.md) - Comprehensive platform guide
- [Prompt Best Practices](./prompt-best-practices.md) - Tips for writing effective prompts

**Need more help?**
- Contact support (feature coming soon)
- Community forums (coming soon)

*Last updated: November 2025*
```

---

### 3. `/home/user/delicious-lotus/docs/prompt-best-practices.md`
**Purpose:** Guide for writing effective prompts

**Content:**
```markdown
# Prompt Best Practices - AI Video Generation

## Introduction

Writing effective prompts is key to getting great AI-generated videos. This guide will teach you how to craft prompts that produce exactly what you envision.

**What is a prompt?**
A prompt is a text description of the video you want to create. Think of it as giving creative direction to a video production team.

**Prompt length:** 500-2000 characters (roughly 100-400 words)

---

## The Anatomy of a Great Prompt

A well-structured prompt includes:

1. **Product/Service** - What you're showcasing
2. **Visual Style** - How it should look
3. **Mood/Tone** - How it should feel
4. **Key Features** - What to highlight
5. **Target Audience** - Who it's for
6. **Specific Scenes** - What to show (optional)

---

## 1. Product/Service Description

**Start with clarity:**
✅ **Good:** "Create a video for an eco-friendly stainless steel water bottle"
❌ **Poor:** "Make a video about a product"

**Be specific:**
✅ **Good:** "Luxury automatic watch with sapphire crystal and Swiss movement"
❌ **Poor:** "Nice watch"

**Include category:**
✅ **Good:** "Fitness app for busy professionals"
❌ **Poor:** "An app"

---

## 2. Visual Style

**Describe the aesthetic:**

**Professional/Corporate:**
"Clean, professional aesthetic with sleek transitions and modern typography"

**Casual/Friendly:**
"Warm, approachable visuals with soft colors and natural lighting"

**Modern/Minimalist:**
"Minimalist design with bold typography, clean lines, and white space"

**Dynamic/Energetic:**
"Fast-paced cuts, vibrant colors, and dynamic camera movements"

**Luxury/Premium:**
"Elegant, sophisticated visuals with gold accents and smooth transitions"

**Examples:**
✅ **Good:** "Modern minimalist style with clean white backgrounds and product-focused shots"
❌ **Poor:** "Make it look good"

---

## 3. Mood and Tone

**Set the emotional tone:**

**Inspiring:**
"Uplifting and motivational, inspiring viewers to take action"

**Exciting:**
"High-energy and exhilarating, building excitement and anticipation"

**Calm:**
"Peaceful and serene, creating a sense of tranquility"

**Professional:**
"Confident and authoritative, establishing credibility"

**Playful:**
"Fun and lighthearted, bringing joy and entertainment"

**Examples:**
✅ **Good:** "Energetic and motivational tone, inspiring people to start their fitness journey"
❌ **Poor:** "Happy vibe"

---

## 4. Key Features and Benefits

**Highlight what matters:**

✅ **Good:** "Emphasize the 24-hour battery life, waterproof design, and premium materials"
❌ **Poor:** "Show the features"

**Focus on benefits:**
✅ **Good:** "Demonstrate how the app saves time and reduces stress for busy professionals"
❌ **Poor:** "Talk about what it does"

**Use sensory language:**
✅ **Good:** "Showcase the smooth, satisfying click of the mechanical keyboard"
❌ **Poor:** "Show it works well"

---

## 5. Target Audience

**Who is this for?**

Including audience helps the AI choose appropriate visuals and messaging.

**Examples:**
- "Targeting young professionals aged 25-35"
- "For eco-conscious millennials"
- "Designed for busy parents"
- "Appealing to luxury watch enthusiasts"
- "Created for small business owners"

✅ **Good:** "Targeting health-conscious millennials who value sustainability"
❌ **Poor:** "For people who might like it"

---

## 6. Specific Scenes (Optional)

**Suggest visual sequences:**

✅ **Good:** "Open with close-up of the product, transition to lifestyle shots of people using it, end with logo and call-to-action"

✅ **Good:** "Show the watch on a wrist, zoom in on the intricate details, pan to a luxury setting"

**Don't be too prescriptive:**
❌ **Poor:** "Camera must be at exactly 45 degrees for the first 3 seconds, then pan left at 2 degrees per second..."

Leave room for AI creativity!

---

## Complete Prompt Examples

### Example 1: Product Ad (Watch)

```
Create a 30-second luxury watch advertisement showcasing an elegant automatic timepiece with a sapphire crystal face and Swiss movement. The visual style should be sophisticated and premium, with dramatic lighting, slow-motion shots, and gold accent colors. Feature close-up details of the intricate watch mechanics, the polished case, and the leather strap. Show the watch in upscale settings - a modern office, a luxury car interior, and an evening event. The mood should be aspirational and exclusive, targeting successful professionals aged 30-50 who appreciate fine craftsmanship. Emphasize precision, heritage, and timeless elegance. End with the brand name and tagline "Time Perfected."
```

**Why it works:**
- Clear product description
- Specific visual style (sophisticated, premium)
- Detailed mood (aspirational, exclusive)
- Target audience identified
- Key features highlighted (mechanics, craftsmanship)
- Suggested scenes without being prescriptive
- Clear ending with CTA

### Example 2: Service Ad (Fitness App)

```
Create an energetic 30-second ad for a fitness app targeting busy professionals. Show diverse people exercising at different times and places - early morning runs, lunch break yoga, evening gym sessions - all using the app on their phones. The visual style should be modern and dynamic with vibrant colors (orange and blue) and fast-paced editing. Emphasize how the app fits into busy schedules with quick 10-minute workouts. The mood should be motivating and empowering, showing real progress and achievement. Include shots of the app interface showing workout tracking, progress graphs, and achievement badges. End with the tagline "Fitness on Your Schedule" and app download call-to-action.
```

**Why it works:**
- Service clearly described
- Visual variety (different times, places)
- Specific color scheme
- Target audience and pain point addressed
- Benefits highlighted (fits busy schedules)
- Motivational mood
- Clear CTA

### Example 3: Event Promotion

```
Create an exciting 45-second video promoting a summer music festival. Open with aerial shots of the festival grounds with colorful tents and stages. Show quick cuts of diverse crowds dancing and enjoying music, performers on stage, food vendors, and festival atmosphere. Visual style should be vibrant and energetic with warm summer colors (yellows, oranges, pinks). Include text overlays with festival dates (July 15-17) and location. Showcase the variety of activities - multiple music stages, art installations, food trucks, and camping areas. The mood should be joyful and exhilarating, capturing the excitement and community of festival life. Target music lovers aged 18-35. End with festival logo, dates, and "Get Your Tickets Now" CTA.
```

**Why it works:**
- Event clearly described
- Specific visual elements (aerial shots, crowds, stages)
- Vibrant color palette
- Key information included (dates, location)
- Variety of festival aspects shown
- Joyful mood conveyed
- Target audience specified
- Strong CTA

---

## Common Mistakes to Avoid

### ❌ Too Vague
**Poor:** "Make a video about my business"
**Better:** "Create a video showcasing our organic coffee roastery, highlighting the artisanal roasting process and sustainable sourcing"

### ❌ Too Technical/Specific
**Poor:** "Camera angle at 37 degrees, focal length 50mm, pan at 1.5 degrees per second, cut at exactly frame 120..."
**Better:** "Cinematic shots with smooth camera movements, focusing on product details"

### ❌ Too Short
**Poor:** "Running shoes ad"
**Better:** "High-energy ad for lightweight running shoes designed for marathon runners, showcasing comfort, breathability, and performance on various terrains"

### ❌ Too Long/Unfocused
**Poor:** A 3000-word essay about your product's entire history and every single feature
**Better:** Focus on 2-3 key selling points and a clear visual narrative (500-2000 characters)

### ❌ Contradictory Instructions
**Poor:** "Modern minimalist style with lots of complex decorative elements and baroque details"
**Better:** Choose one consistent style: "Modern minimalist style with clean lines and simple elegance"

### ❌ Inappropriate Content
**Poor:** Prompts with violence, adult content, copyrighted characters, or misleading claims
**Better:** Original, appropriate content that follows platform guidelines

---

## Tips by Video Type

### Product Showcase

**Focus on:**
- Product details and features
- Usage scenarios
- Benefits and value proposition
- Quality and craftsmanship

**Example structure:**
1. Product introduction
2. Key features demonstrated
3. Lifestyle/usage shots
4. Brand and CTA

### Service Promotion

**Focus on:**
- Problem the service solves
- How it works
- Benefits and outcomes
- Target customer scenarios

**Example structure:**
1. Show the problem
2. Introduce the solution
3. Demonstrate benefits
4. Call to action

### Brand Story

**Focus on:**
- Brand values and mission
- Emotional connection
- Visual identity
- Brand personality

**Example structure:**
1. Set the scene/mood
2. Tell the story
3. Showcase values
4. Brand message

### Event Promotion

**Focus on:**
- Event atmosphere and energy
- Key activities and attractions
- Dates, location, logistics
- Why people should attend

**Example structure:**
1. Capture attention with energy
2. Show event highlights
3. Include key details
4. Strong CTA for tickets

---

## Advanced Techniques

### 1. Use Sensory Language

**Instead of:** "The coffee is good"
**Try:** "Rich, aromatic coffee with notes of chocolate and caramel"

**Instead of:** "Comfortable chair"
**Try:** "Plush, ergonomic chair with memory foam cushioning"

### 2. Show Don't Tell

**Instead of:** "Our app is easy to use"
**Try:** "Show someone effortlessly navigating the app interface with intuitive swipes and taps"

**Instead of:** "High-quality materials"
**Try:** "Showcase the brushed aluminum finish catching light, and the premium leather grain texture"

### 3. Create Visual Contrast

**Technique:** Before and after, problem and solution, old vs. new

**Example:** "Open with chaotic, stressful morning routine, transition to calm, organized morning using the app"

### 4. Use Metaphors and Symbolism

**Example:** "Visualize speed with quick cuts and motion blur, symbolize security with a vault or shield imagery"

**Example:** "Use sunrise to represent new beginnings, growth through blooming flowers"

### 5. Specify Transitions

**Example:** "Smooth fade transitions between scenes for a calming effect"
**Example:** "Quick cut transitions for energetic, dynamic pacing"
**Example:** "Zoom transitions focusing from wide shot to product details"

### 6. Color Psychology

**Red:** Energy, passion, urgency
**Blue:** Trust, calm, professional
**Green:** Nature, health, growth
**Yellow:** Optimism, happiness, attention
**Purple:** Luxury, creativity, wisdom
**Orange:** Enthusiasm, confidence, friendly
**Black/White:** Elegance, simplicity, sophistication

**Example:** "Use deep blues and whites for a trustworthy, professional tech brand"

---

## Prompt Checklist

Before submitting, ask yourself:

- [ ] Have I clearly described what the video is about?
- [ ] Have I specified the visual style?
- [ ] Have I conveyed the mood and tone?
- [ ] Have I highlighted key features or benefits?
- [ ] Have I identified the target audience?
- [ ] Is my prompt 500-2000 characters?
- [ ] Have I avoided vague or contradictory language?
- [ ] Have I avoided copyrighted or inappropriate content?
- [ ] Have I included specific details without being too prescriptive?
- [ ] Have I considered colors, pacing, and transitions?

---

## Iteration and Refinement

**Don't expect perfection on first try!**

1. **Generate:** Create your first video
2. **Review:** Watch and note what works and what doesn't
3. **Refine:** Adjust your prompt based on results
4. **Regenerate:** Try again with improvements
5. **Compare:** See the difference

**Example iteration:**

**First attempt:**
"Create a video for a coffee shop"

**After review - too generic, add detail:**
"Create a warm, inviting video for an artisanal coffee shop highlighting hand-poured coffee, cozy atmosphere, and community space"

**After second review - add more visual detail:**
"Create a warm, inviting 30-second video for an artisanal coffee shop. Show close-ups of skilled baristas hand-pouring coffee with latte art, steam rising from fresh cups, customers relaxing in cozy seating with warm lighting. Visual style should be natural and authentic with earth tones (browns, creams, warm whites). Mood is welcoming and community-focused, targeting coffee enthusiasts who value quality and craft. End with shop name and 'Your Daily Ritual' tagline."

---

## Prompt Templates

### Template 1: Product Ad
```
Create a [duration]-second [style] video for [product name], a [product category] designed for [target audience]. Showcase [key features] through [type of shots]. The visual style should be [aesthetic description] with [color palette]. The mood should be [emotional tone], emphasizing [key benefits]. Include [specific scenes or elements]. End with [brand name] and [CTA].
```

### Template 2: Service Ad
```
Create a [duration]-second video promoting [service name], a [service type] for [target audience]. Show [problem or pain point] and how the service provides [solution]. Visual style should be [aesthetic] with [pacing description]. Feature [specific demonstrations or scenarios]. The tone should be [mood], highlighting [key benefits]. Include [service features or interface]. End with [tagline] and [CTA].
```

### Template 3: Brand Story
```
Create a [duration]-second brand video for [company name] that tells the story of [brand mission or values]. Open with [establishing scene], then show [key brand elements or activities]. The visual style should be [aesthetic] reflecting [brand personality]. Use [color scheme] consistent with brand identity. The mood should be [emotional tone], connecting with [target audience] who value [audience values]. End with [brand message] and logo.
```

---

## Final Tips

1. **Start Simple:** Begin with a straightforward prompt, add complexity as you learn
2. **Be Descriptive:** More detail usually yields better results
3. **Stay Focused:** One clear message is better than many competing ideas
4. **Use Examples:** Reference styles or moods from other media (but don't copy)
5. **Think Visually:** Describe what you see, not just what you want to say
6. **Test Variations:** Try different approaches to the same concept
7. **Learn from Results:** Each generation teaches you what works
8. **Have Fun:** Experiment and be creative!

---

## Resources

- **User Guide:** Learn how to use the platform
- **FAQ:** Answers to common questions
- **Example Gallery:** See videos generated from various prompts (coming soon)

---

*Happy creating! Your perfect video is just a great prompt away.*

*Last updated: November 2025*
```

---

### 4. `/home/user/delicious-lotus/frontend/src/components/HelpTooltip.tsx`
**Purpose:** In-app help tooltip component

**Component Interface:**
```typescript
export interface HelpTooltipProps {
  content: string | React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

export function HelpTooltip({
  content,
  position = 'top',
  className,
}: HelpTooltipProps): JSX.Element {
  const [isVisible, setIsVisible] = useState(false);
  
  return (
    <div className={`help-tooltip ${className}`}>
      <button
        className="help-tooltip__trigger"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        aria-label="Help"
        type="button"
      >
        <QuestionIcon className="help-tooltip__icon" />
      </button>
      
      {isVisible && (
        <div
          className={`help-tooltip__content help-tooltip__content--${position}`}
          role="tooltip"
        >
          {content}
        </div>
      )}
    </div>
  );
}
```

**Features:**
- Question mark icon (?)
- Hover to show tooltip
- Keyboard accessible (focus to show)
- Positioning (top, bottom, left, right)
- Supports text or React nodes

**Styling:**
```css
.help-tooltip {
  position: relative;
  display: inline-block;
}

.help-tooltip__trigger {
  background: none;
  border: none;
  padding: 0;
  cursor: help;
  color: var(--color-text-secondary);
  transition: color 0.2s;
}

.help-tooltip__trigger:hover,
.help-tooltip__trigger:focus {
  color: var(--color-primary);
}

.help-tooltip__icon {
  width: 16px;
  height: 16px;
}

.help-tooltip__content {
  position: absolute;
  z-index: 1000;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  box-shadow: var(--shadow-lg);
  font-size: 14px;
  line-height: 1.5;
  max-width: 250px;
  white-space: normal;
  pointer-events: none;
}

.help-tooltip__content--top {
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 8px;
}

.help-tooltip__content--bottom {
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 8px;
}

.help-tooltip__content--left {
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  margin-right: 8px;
}

.help-tooltip__content--right {
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  margin-left: 8px;
}
```

---

### 5. `/home/user/delicious-lotus/frontend/src/data/helpContent.ts`
**Purpose:** Help content data structure

**Content Structure:**
```typescript
export interface HelpContent {
  id: string;
  title: string;
  content: string;
  link?: string;
}

export const helpContent: Record<string, HelpContent> = {
  // Generation Form
  prompt: {
    id: 'prompt',
    title: 'Writing Effective Prompts',
    content: 'Describe your video in detail (500-2000 characters). Include product/service, visual style, mood, key features, and target audience.',
    link: '/docs/prompt-best-practices',
  },
  
  brandName: {
    id: 'brandName',
    title: 'Brand Name',
    content: 'Enter your company or product name. This helps the AI understand your brand identity and may appear in the video.',
  },
  
  logo: {
    id: 'logo',
    title: 'Logo Upload',
    content: 'Upload your brand logo (JPEG or PNG, max 50MB). Use high-resolution images (at least 512x512). PNG with transparent background works best.',
  },
  
  brandColors: {
    id: 'brandColors',
    title: 'Brand Colors',
    content: 'Select your primary and secondary brand colors. These influence the video\'s color palette, backgrounds, and text overlays.',
  },
  
  cta: {
    id: 'cta',
    title: 'Call-to-Action',
    content: 'Add a call-to-action at the end of your video (e.g., "Shop Now", "Learn More", "Sign Up"). Keep it short and action-oriented.',
  },
  
  duration: {
    id: 'duration',
    title: 'Video Duration',
    content: '15s: Quick ads | 30s: Standard (recommended) | 45s: Detailed showcase | 60s: Full story',
  },
  
  aspectRatio: {
    id: 'aspectRatio',
    title: 'Aspect Ratio',
    content: '16:9 (Landscape): YouTube, websites | 9:16 (Portrait): Instagram Stories, TikTok | 1:1 (Square): Instagram/Facebook feeds',
  },
  
  style: {
    id: 'style',
    title: 'Visual Style',
    content: 'Professional: Corporate, polished | Casual: Friendly, approachable | Modern: Sleek, minimalist | Dynamic: Energetic, fast-paced',
  },
  
  musicStyle: {
    id: 'musicStyle',
    title: 'Music Style',
    content: 'Corporate: Professional, upbeat | Upbeat: Energetic, positive | Cinematic: Epic, dramatic | Ambient: Calm, subtle',
  },
  
  // Progress Page
  progress: {
    id: 'progress',
    title: 'Generation Progress',
    content: 'Your video is being generated. Keep this tab open to see real-time updates. Typical generation takes 3-7 minutes.',
  },
  
  cancel: {
    id: 'cancel',
    title: 'Cancel Generation',
    content: 'You can cancel generation at any time. This will stop the process immediately. Cancelled generations don\'t count against quotas.',
  },
  
  // History Page
  status: {
    id: 'status',
    title: 'Generation Status',
    content: 'Completed ✅ | Processing ⏳ | Composing 🔄 | Queued ⏸ | Failed ❌ | Cancelled 🚫',
  },
  
  rerun: {
    id: 'rerun',
    title: 'Re-run Generation',
    content: 'Create a new video with the same settings as this generation. You can modify the prompt or settings before generating.',
  },
  
  // Preview Page
  download: {
    id: 'download',
    title: 'Download Video',
    content: 'Download your video as MP4 (1080p, H.264). Compatible with all major platforms. File size typically 5-25MB depending on duration.',
  },
  
  playbackSpeed: {
    id: 'playbackSpeed',
    title: 'Playback Speed',
    content: 'Adjust preview playback speed (0.5x to 2x). This only affects the preview, not the downloaded video.',
  },
};

// Helper function to get help content
export function getHelpContent(id: string): HelpContent | undefined {
  return helpContent[id];
}

// Helper function to create tooltip element
export function createTooltip(id: string): React.ReactNode {
  const content = getHelpContent(id);
  if (!content) return null;
  
  return (
    <HelpTooltip content={content.content}>
      {content.link && (
        <a href={content.link} target="_blank" rel="noopener noreferrer">
          Learn more
        </a>
      )}
    </HelpTooltip>
  );
}
```

---

## Files to Modify

None - all new files for documentation.

---

## Dependencies

### NPM Packages
None

### Internal Dependencies
- `/frontend/src/components/ui/Button.tsx` - For help button styling
- Design system CSS variables

---

## API Integration

No API integration required. Documentation is static content.

---

## Implementation Details

### Step 1: Create User Guide (45 minutes)
1. Create `docs/user-guide.md`
2. Write comprehensive sections (Getting Started, Creating Videos, etc.)
3. Include screenshots placeholders
4. Add examples and tips
5. Proofread for clarity

### Step 2: Create FAQ (30 minutes)
1. Create `docs/faq.md`
2. Organize by categories
3. Write 15-20 common questions
4. Provide clear, actionable answers
5. Add links to other docs

### Step 3: Create Prompt Best Practices (30 minutes)
1. Create `docs/prompt-best-practices.md`
2. Write structure guide
3. Add complete prompt examples
4. Include common mistakes
5. Add prompt templates

### Step 4: Create HelpTooltip Component (15 minutes)
1. Create `components/HelpTooltip.tsx`
2. Build tooltip with positioning
3. Add keyboard accessibility
4. Style with design system
5. Test hover and focus

### Step 5: Create Help Content Data (10 minutes)
1. Create `data/helpContent.ts`
2. Define help content for each field
3. Add helper functions
4. Export for use in components

---

## Acceptance Criteria

- [ ] User guide covering:
  - [ ] Getting started
  - [ ] Creating your first Ad Creative video
  - [ ] Understanding the generation process
  - [ ] Using brand assets (logo, colors)
  - [ ] Configuring video parameters (duration, aspect ratio)
  - [ ] Downloading and sharing videos
  - [ ] Troubleshooting common issues
- [ ] FAQ with 15+ questions:
  - [ ] What is the maximum video duration?
  - [ ] What aspect ratios are supported?
  - [ ] How long does generation take?
  - [ ] What file formats can I upload?
  - [ ] Can I cancel a generation?
  - [ ] How do I write better prompts?
  - [ ] What if generation fails?
  - [ ] And more...
- [ ] Prompt best practices guide:
  - [ ] Structure of effective prompts
  - [ ] Example prompts for different ad types (product, service, event)
  - [ ] How to describe brand identity
  - [ ] Tips for visual consistency
  - [ ] Common mistakes to avoid
  - [ ] Character limit guidelines (500-2000 chars)
- [ ] HelpTooltip component:
  - [ ] Question mark icon with popover
  - [ ] Hover to show
  - [ ] Keyboard accessible
  - [ ] Multiple positioning options
- [ ] Help content data structure for in-app tooltips

---

## Testing Approach

### Documentation Review
1. **Readability:**
   - Clear, non-technical language
   - Logical organization
   - Proper formatting

2. **Accuracy:**
   - All information correct
   - Links work
   - Examples are valid

3. **Completeness:**
   - All major topics covered
   - No broken references
   - All questions answered

### Component Tests
1. **HelpTooltip:**
   - Renders icon
   - Shows on hover
   - Shows on focus
   - Positions correctly
   - Accessible

### User Testing
1. **Usability:**
   - Can new users understand?
   - Is navigation intuitive?
   - Are examples helpful?
   - Is tone appropriate?

---

## Success Criteria

This PR is successful when:
1. All documentation files created
2. Content is clear and comprehensive
3. HelpTooltip component works
4. Help content data structured
5. No typos or errors
6. Examples are effective
7. Tone is user-friendly
8. All acceptance criteria met
9. Proofread and polished
10. Ready for user reference
