export interface HelpContent {
  title: string;
  content: string;
  links?: Array<{
    url: string;
    text: string;
  }>;
}

// Help content database
const helpContentMap: Record<string, HelpContent> = {
  // Add help content items here as needed
};

/**
 * Get help content by ID
 * @param id - Help content ID
 * @returns Help content object or null if not found
 */
export function getHelpById(id: string): HelpContent | null {
  return helpContentMap[id] || null;
}
