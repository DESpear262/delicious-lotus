import { NavLink } from 'react-router-dom';
import styles from './Navigation.module.css';

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
    { path: '/history', label: 'History' },
  ];

  const handleLinkClick = () => {
    if (isMobile && onClose) {
      onClose();
    }
  };

  return (
    <nav
      className={`${styles.navigation} ${isMobile ? styles.navigationMobile : ''}`}
      role="navigation"
      aria-label="Main navigation"
    >
      <ul className={styles.navigationList}>
        {navItems.map((item) => (
          <li key={item.path} className={styles.navigationItem}>
            <NavLink
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `${styles.navigationLink} ${isActive ? styles.navigationLinkActive : ''}`
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
