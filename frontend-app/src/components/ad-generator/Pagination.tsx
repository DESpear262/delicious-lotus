import React from 'react';
import { Button } from '@/components/ad-generator/ui/Button';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  onItemsPerPageChange: (itemsPerPage: number) => void;
  itemsPerPageOptions?: number[];
}

const DEFAULT_ITEMS_PER_PAGE_OPTIONS = [20, 50, 100];

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  onItemsPerPageChange,
  itemsPerPageOptions = DEFAULT_ITEMS_PER_PAGE_OPTIONS,
}) => {
  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  const handlePageClick = (page: number) => {
    onPageChange(page);
  };

  const handleItemsPerPageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onItemsPerPageChange(Number(e.target.value));
  };

  // Generate page numbers to display
  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    const maxPagesToShow = 7;

    if (totalPages <= maxPagesToShow) {
      // Show all pages
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show first page
      pages.push(1);

      if (currentPage <= 3) {
        // Near the beginning
        for (let i = 2; i <= 5; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        // Near the end
        pages.push('...');
        for (let i = totalPages - 4; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        // Middle
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  };

  const pageNumbers = getPageNumbers();
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  if (totalPages === 0) {
    return null;
  }

  return (
    <div className="flex items-center justify-between gap-4 p-4 border-t border-border bg-background md:flex-col md:gap-3 md:p-2">
      {/* Items per page selector */}
      <div className="flex items-center gap-2 md:w-full md:justify-between">
        <label htmlFor="items-per-page" className="text-sm text-muted-foreground whitespace-nowrap">
          Items per page:
        </label>
        <select
          id="items-per-page"
          value={itemsPerPage}
          onChange={handleItemsPerPageChange}
          className="py-2 px-3 border border-border rounded-md text-sm text-foreground bg-background cursor-pointer transition-colors hover:border-primary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
        >
          {itemsPerPageOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      {/* Page info */}
      <div className="text-sm text-muted-foreground whitespace-nowrap md:w-full md:text-center">
        Showing {startItem}-{endItem} of {totalItems}
      </div>

      {/* Page controls */}
      <div className="flex items-center gap-2 md:w-full md:flex-wrap md:justify-center">
        <Button
          variant="outline"
          size="sm"
          onClick={handlePrevious}
          disabled={currentPage === 1}
          aria-label="Previous page"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Previous
        </Button>

        <div className="flex items-center gap-1 md:order-first md:w-full md:justify-center md:mb-2 md:gap-0">
          {pageNumbers.map((page, index) =>
            page === '...' ? (
              <span key={`ellipsis-${index}`} className="p-2 text-muted-foreground text-sm select-none">
                ...
              </span>
            ) : (
              <button
                key={page}
                onClick={() => handlePageClick(page as number)}
                className={`min-w-[36px] h-9 p-2 border rounded-md text-sm font-medium cursor-pointer transition-all md:min-w-[32px] md:h-8 md:text-xs ${currentPage === page
                    ? 'bg-primary text-primary-foreground border-primary hover:bg-primary/90'
                    : 'bg-background text-foreground border-border hover:bg-muted hover:border-border/80'
                  } ${
                  // Hide intermediate pages on mobile, keeping first, last, current, and adjacent
                  typeof page === 'number' &&
                    page !== 1 &&
                    page !== totalPages &&
                    page !== currentPage &&
                    Math.abs(page - currentPage) > 1
                    ? 'md:hidden'
                    : ''
                  }`}
                aria-label={`Go to page ${page}`}
                aria-current={currentPage === page ? 'page' : undefined}
              >
                {page}
              </button>
            )
          )}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={handleNext}
          disabled={currentPage === totalPages}
          aria-label="Next page"
        >
          Next
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </Button>
      </div>
    </div>
  );
};
