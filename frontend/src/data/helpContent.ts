/**
 * Help content data for in-app tooltips and guidance
 * Organized by page/feature for easy maintenance and retrieval
 */

export interface HelpContent {
  id: string;
  title: string;
  content: string;
  links?: Array<{
    text: string;
    url: string;
  }>;
}

export interface HelpSection {
  section: string;
  items: HelpContent[];
}

/**
 * All help content organized by section
 */
export const helpContent: HelpSection[] = [
  {
    section: 'pipeline-selection',
    items: [
      {
        id: 'pipeline-ad-creative',
        title: 'Ad Creative Pipeline',
        content:
          'Create short-form video advertisements (15-60 seconds) perfect for social media, marketing campaigns, and promotional content. Upload your brand assets and describe your vision to generate professional video ads.',
        links: [
          {
            text: 'Learn More',
            url: '/docs/user-guide#creating-your-first-ad-creative-video',
          },
        ],
      },
      {
        id: 'pipeline-music-video',
        title: 'Music Video Pipeline (Coming Soon)',
        content:
          'Generate longer music videos (60-180 seconds) synchronized with your audio track. Perfect for artists, promotional content, and creative projects. This feature will be available in a future update.',
      },
    ],
  },
  {
    section: 'prompt-input',
    items: [
      {
        id: 'prompt-basics',
        title: 'Writing Effective Prompts',
        content:
          'Your prompt is the creative direction for your video. Describe what you want to see, the mood and feeling, your target audience, and your call-to-action. Be specific but not overly restrictive. Think of it as briefing a video production team.',
        links: [
          {
            text: 'Prompt Best Practices',
            url: '/docs/prompt-best-practices',
          },
        ],
      },
      {
        id: 'prompt-length',
        title: 'Character Limits',
        content:
          'Prompts must be between 500-2000 characters. The sweet spot is 800-1200 characters - detailed enough to guide the AI, but focused enough to maintain clarity. Too short lacks detail; too long may include conflicting instructions.',
      },
      {
        id: 'prompt-examples',
        title: 'Example Prompts',
        content:
          'Good prompts include: the main message, visual style (colors, lighting, pace), target audience, brand personality, and call-to-action. Example: "Create an energetic 30-second ad for running shoes. Show urban runners at sunrise with bold colors and fast transitions. Target young professionals. End with logo and tagline \'Run Your World\'."',
        links: [
          {
            text: 'View More Examples',
            url: '/docs/prompt-best-practices#example-prompts-by-use-case',
          },
        ],
      },
    ],
  },
  {
    section: 'brand-assets',
    items: [
      {
        id: 'logo-upload',
        title: 'Logo Upload',
        content:
          'Upload your brand logo to include in your video. For best results, use PNG format with transparent background. Logo should be high resolution (at least 1000px wide). Your logo will typically appear at the start or end of the video.',
      },
      {
        id: 'product-images',
        title: 'Product Images',
        content:
          'Upload high-quality images of your products (JPEG or PNG, max 50MB each). Use clean professional photography with simple backgrounds. You can upload multiple images - the AI will select and incorporate the best ones into your video.',
      },
      {
        id: 'file-requirements',
        title: 'File Requirements',
        content:
          'Supported formats: JPEG, PNG. Maximum size: 50MB per file. Recommended dimensions: At least 1920x1080 pixels. For logos, PNG with transparent background works best.',
      },
      {
        id: 'brand-colors',
        title: 'Brand Colors',
        content:
          'Specify your brand colors (up to 3) using the color picker or hex codes. The AI will incorporate these colors into backgrounds, overlays, transitions, and visual accents to maintain your brand identity throughout the video.',
      },
    ],
  },
  {
    section: 'video-parameters',
    items: [
      {
        id: 'duration',
        title: 'Video Duration',
        content:
          'Choose between 15-60 seconds for Ad Creative videos. Shorter videos (15-30s) work best for social media and have higher completion rates. Longer videos (45-60s) allow for more detailed storytelling and product showcases.',
      },
      {
        id: 'aspect-ratio',
        title: 'Aspect Ratio',
        content:
          '16:9 (Landscape) - Best for YouTube, websites, presentations. 9:16 (Portrait) - Perfect for Instagram Stories, TikTok, mobile. 1:1 (Square) - Great for Instagram feed, Facebook, LinkedIn. Choose based on where you\'ll share your video.',
        links: [
          {
            text: 'Aspect Ratio Guide',
            url: '/docs/user-guide#aspect-ratio-guide',
          },
        ],
      },
      {
        id: 'cta-text',
        title: 'Call-to-Action Text',
        content:
          'Optional text that appears at the end of your video (e.g., "Shop Now", "Learn More", "Visit Website"). Keep it short and action-oriented (2-4 words). This gives viewers a clear next step.',
      },
    ],
  },
  {
    section: 'generation-process',
    items: [
      {
        id: 'generation-time',
        title: 'How Long Does It Take?',
        content:
          'Video generation typically takes 4-12 minutes depending on duration, complexity, and server load. You can watch real-time progress as the AI validates input, plans content, generates clips, and composes the final video.',
      },
      {
        id: 'generation-stages',
        title: 'Generation Stages',
        content:
          'Your video goes through 5 stages: (1) Input Validation - checking your prompt and files, (2) Content Planning - AI creates shot-by-shot plan, (3) Asset Generation - creating individual clips, (4) Video Composition - assembling clips with transitions, (5) Final Rendering - encoding to MP4.',
        links: [
          {
            text: 'Detailed Process',
            url: '/docs/user-guide#understanding-the-generation-process',
          },
        ],
      },
      {
        id: 'cancel-generation',
        title: 'Canceling Generation',
        content:
          'You can cancel generation at any time by clicking "Cancel Generation". The process will stop immediately. Note that you cannot resume a canceled job - you\'ll need to submit a new request if you want to try again.',
      },
      {
        id: 'progress-tracking',
        title: 'Progress Updates',
        content:
          'Watch real-time progress showing current stage, percentage complete, individual clip progress (e.g., "5/10 clips"), and estimated time remaining. The progress bar updates automatically as generation proceeds.',
      },
    ],
  },
  {
    section: 'video-preview',
    items: [
      {
        id: 'preview-player',
        title: 'Video Preview',
        content:
          'Once generation completes, preview your video in the built-in player. Use standard playback controls: play/pause, seek timeline, volume, fullscreen. Keyboard shortcuts: Space (play/pause), ← → (seek), F (fullscreen), M (mute).',
      },
      {
        id: 'download',
        title: 'Download Your Video',
        content:
          'Click "Download Video" to save your MP4 file (H.264, 720p HD). File size typically ranges from 5-20MB depending on duration. Videos are optimized for web and social media use.',
      },
      {
        id: 'video-quality',
        title: 'Video Specifications',
        content:
          'All videos are delivered as MP4 files with H.264 codec at 720p HD resolution. This format is compatible with all major platforms and provides excellent quality while keeping file sizes reasonable for sharing.',
      },
    ],
  },
  {
    section: 'troubleshooting',
    items: [
      {
        id: 'generation-failed',
        title: 'Generation Failed',
        content:
          'If generation fails, check the error message for details. Common causes: invalid file formats, corrupted uploads, network interruption, or server issues. Try verifying your files and prompt, then submit again after a few minutes.',
        links: [
          {
            text: 'Troubleshooting Guide',
            url: '/docs/user-guide#troubleshooting-common-issues',
          },
          {
            text: 'FAQ',
            url: '/docs/faq#troubleshooting',
          },
        ],
      },
      {
        id: 'upload-failed',
        title: 'Upload Issues',
        content:
          'If uploads fail, check: (1) File size under 50MB, (2) Format is JPEG or PNG, (3) Internet connection is stable, (4) File is not corrupted. Try a different file or browser if problems persist.',
      },
      {
        id: 'poor-quality',
        title: 'Improving Results',
        content:
          'For better results: (1) Write more specific, detailed prompts, (2) Upload higher quality brand assets, (3) Study example prompts, (4) Avoid conflicting instructions. Each generation is unique - try again with refinements.',
        links: [
          {
            text: 'Prompt Best Practices',
            url: '/docs/prompt-best-practices',
          },
        ],
      },
      {
        id: 'slow-generation',
        title: 'Slow Generation',
        content:
          'Generation may take longer during peak usage, for complex prompts, or longer videos. Be patient - quality takes time! If stuck for more than 20 minutes, try canceling and resubmitting. Avoid refreshing the page.',
      },
    ],
  },
  {
    section: 'general',
    items: [
      {
        id: 'getting-started',
        title: 'Getting Started',
        content:
          'New to the platform? Start by selecting Ad Creative pipeline, write a detailed description of your desired video (500-2000 characters), upload your brand logo and assets, configure duration and aspect ratio, then submit. Generation takes 4-12 minutes.',
        links: [
          {
            text: 'Complete User Guide',
            url: '/docs/user-guide',
          },
          {
            text: 'Quick Start',
            url: '/docs/user-guide#quick-start',
          },
        ],
      },
      {
        id: 'best-practices',
        title: 'Best Practices',
        content:
          'For best results: (1) Be specific in your prompts, (2) Upload high-quality brand assets, (3) Choose appropriate duration and aspect ratio for your platform, (4) Review settings before submitting, (5) Study example prompts to learn what works.',
      },
      {
        id: 'support',
        title: 'Need Help?',
        content:
          'Browse our comprehensive documentation including User Guide, FAQ, and Prompt Best Practices. Look for help icons (?) throughout the platform for quick tips. Contact support@ai-video-platform.com for additional assistance.',
        links: [
          {
            text: 'User Guide',
            url: '/docs/user-guide',
          },
          {
            text: 'FAQ',
            url: '/docs/faq',
          },
          {
            text: 'Prompt Best Practices',
            url: '/docs/prompt-best-practices',
          },
        ],
      },
    ],
  },
];

/**
 * Get help content by ID
 */
export function getHelpById(id: string): HelpContent | undefined {
  for (const section of helpContent) {
    const item = section.items.find((item) => item.id === id);
    if (item) return item;
  }
  return undefined;
}

/**
 * Get all help content for a specific section
 */
export function getHelpBySection(sectionName: string): HelpContent[] {
  const section = helpContent.find((s) => s.section === sectionName);
  return section ? section.items : [];
}

/**
 * Search help content by keyword
 */
export function searchHelp(keyword: string): HelpContent[] {
  const lowerKeyword = keyword.toLowerCase();
  const results: HelpContent[] = [];

  for (const section of helpContent) {
    for (const item of section.items) {
      if (
        item.title.toLowerCase().includes(lowerKeyword) ||
        item.content.toLowerCase().includes(lowerKeyword)
      ) {
        results.push(item);
      }
    }
  }

  return results;
}

/**
 * Get quick tips for specific contexts
 */
export const quickTips = {
  promptWriting: [
    'Be specific about visual style, mood, and pacing',
    'Include your target audience and purpose',
    'Describe what you want to see, not technical camera details',
    'Keep prompts between 800-1200 characters for best results',
    'End with a clear call-to-action',
  ],
  brandAssets: [
    'Use PNG with transparent background for logos',
    'Upload high-resolution images (1920x1080 or larger)',
    'Professional photography works better than casual snapshots',
    'Specify 2-3 brand colors for consistent visual identity',
  ],
  videoSettings: [
    'Choose 16:9 for YouTube and websites',
    'Use 9:16 for Instagram Stories and TikTok',
    'Select 1:1 square for Instagram feed and Facebook',
    'Shorter videos (15-30s) have higher completion rates',
    'Match duration to your platform and message complexity',
  ],
  generation: [
    'Typical generation time is 4-12 minutes',
    'You can watch real-time progress updates',
    'Cancel anytime if you need to make changes',
    'Avoid refreshing the page during generation',
  ],
};

export default helpContent;
