import { Link } from 'react-router-dom';
import styles from './Breadcrumbs.module.css';

export interface BreadcrumbItem {
  label: string;
  path?: string;
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

/**
 * Breadcrumbs Component
 *
 * Displays a breadcrumb navigation trail showing the current page's hierarchy.
 * The last item (current page) is not a link and has aria-current="page".
 *
 * @param items - Array of breadcrumb items with label and optional path
 *
 * @example
 * <Breadcrumbs items={[
 *   { label: 'Home', path: '/' },
 *   { label: 'History', path: '/history' },
 *   { label: 'Generation Details' }
 * ]} />
 */
export function Breadcrumbs({ items }: BreadcrumbsProps) {
  if (!items || items.length === 0) {
    return <></>;
  }

  return (
    <nav className={styles.breadcrumbs} aria-label="Breadcrumb">
      <ol className={styles.breadcrumbsList}>
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={index} className={styles.breadcrumbsItem}>
              {item.path && !isLast ? (
                <Link to={item.path} className={styles.breadcrumbsLink}>
                  {item.label}
                </Link>
              ) : (
                <span
                  className={styles.breadcrumbsCurrent}
                  aria-current={isLast ? 'page' : undefined}
                >
                  {item.label}
                </span>
              )}
              {!isLast && (
                <span className={styles.breadcrumbsSeparator} aria-hidden="true">
                  /
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
