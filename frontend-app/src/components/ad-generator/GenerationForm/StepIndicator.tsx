import React from 'react';

interface StepIndicatorProps {
  currentStep: number;
  completedSteps: number[];
  onStepClick: (step: number) => void;
}

const STEPS = [
  { id: 1, title: 'Prompt', description: 'Describe your video' },
  { id: 2, title: 'Brand', description: 'Logo & Colors' },
  { id: 3, title: 'Settings', description: 'Duration & Style' },
  { id: 4, title: 'Review', description: 'Final Check' },
];

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  completedSteps,
  onStepClick,
}) => {
  return (
    <div className="flex items-start justify-between mb-8 relative md:flex-col md:gap-4">
      {STEPS.map((step, index) => {
        const isCompleted = completedSteps.includes(step.id);
        const isActive = currentStep === step.id;
        const isClickable = isCompleted || isActive;
        const isLast = index === STEPS.length - 1;

        return (
          <div key={step.id} className={`flex-1 flex items-start relative md:w-full ${isCompleted ? 'text-green-500' : ''}`}>
            <button
              className={`flex flex-col items-center gap-2 bg-none border-none p-0 text-center w-full md:flex-row md:justify-start md:text-left md:gap-3
                ${isClickable ? 'cursor-pointer group' : 'cursor-default'}
                ${!isClickable && !isActive ? 'opacity-60 cursor-not-allowed' : ''}
              `}
              onClick={() => isClickable && onStepClick(step.id)}
              disabled={!isClickable}
              type="button"
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-base transition-all border-2
                  ${isCompleted
                    ? 'bg-green-500 text-white border-green-500'
                    : isActive
                      ? 'bg-primary text-white border-primary ring-4 ring-blue-500/10'
                      : 'bg-muted text-muted-foreground border-transparent'
                  }
                  ${isClickable ? 'group-hover:scale-105' : ''}
                `}
              >
                {isCompleted ? (
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : (
                  step.id
                )}
              </div>
              <div className="flex flex-col gap-1 max-w-[120px] md:max-w-none md:items-start">
                <span className={`text-sm font-medium leading-tight ${isActive ? 'text-primary font-semibold' : 'text-foreground'}`}>
                  {step.title}
                </span>
                <span className="text-xs text-muted-foreground leading-tight">
                  {step.description}
                </span>
              </div>
            </button>
            {!isLast && (
              <div className={`absolute top-5 left-1/2 w-full h-[2px] -z-10 md:hidden ${isCompleted ? 'bg-green-500' : 'bg-border'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
};
