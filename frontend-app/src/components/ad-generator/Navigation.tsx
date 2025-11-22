import { NavLink } from 'react-router-dom';
import { ROUTES } from '../../types/routes';

interface NavigationProps {
  isMobile?: boolean;
  onClose?: () => void;
}

interface NavItem {
  path: string;
  label: string;
}

/**
 * Navigation Component
 *
 * Primary navigation menu with support for both desktop and mobile layouts.
 * Uses NavLink for automatic active route highlighting.
 *
 * @param isMobile - If true, renders mobile-optimized layout
 * @param onClose - Callback function to close mobile menu on link click
 */
export function Navigation({ isMobile = false, onClose }: NavigationProps) {
  const navItems: NavItem[] = [
    { path: '/', label: 'Home' },
    { path: `${ROUTES.AD_GENERATOR}/history`, label: 'History' },
  ];

  const handleLinkClick = () => {
    if (isMobile && onClose) {
      onClose();
    }
  };

  return (
    <nav
      className={`flex items-center ${isMobile ? 'w-full' : ''}`}
      role="navigation"
      aria-label="Main navigation"
    >
      <ul className={`flex list-none m-0 p-0 ${isMobile ? 'flex-col gap-0 w-full' : 'gap-2'}`}>
        {navItems.map((item) => (
          <li key={item.path} className="m-0">
            <NavLink
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `block transition-all font-medium
                ${isMobile
                  ? 'px-6 py-4 border-l-[3px] hover:bg-secondary text-lg'
                  : 'px-4 py-2 border-b-2 hover:text-primary rounded-sm'
                }
                ${isActive
                  ? isMobile
                    ? 'border-l-primary bg-secondary text-primary font-semibold'
                    : 'border-primary text-primary font-semibold'
                  : isMobile
                    ? 'border-transparent text-foreground/80'
                    : 'border-transparent text-foreground/80'
                }`
              }
              onClick={handleLinkClick}
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
