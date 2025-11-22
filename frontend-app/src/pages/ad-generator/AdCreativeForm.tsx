import React from 'react';
import { useGenerationForm } from '@/hooks/ad-generator/useGenerationForm';
import { isStepComplete } from '@/utils/ad-generator/formValidation';
import {
  FormContainer,
  StepIndicator,
  PromptInput,
  BrandSettings,
  VideoParameters,
  ReviewStep,
} from '@/components/ad-generator/GenerationForm';
import { ConfirmDialog } from '@/components/ad-generator/ui/ConfirmDialog';

export const AdCreativeForm: React.FC = () => {
  const {
    currentStep,
    formData,
    errors,
    isSubmitting,
    submitError,
    updateField,
    handleFieldBlur,
    nextStep,
    previousStep,
    goToStep,
    submitForm,
    showRestoreDialog,
    handleResume,
    handleDiscard,
  } = useGenerationForm();

  // Calculate completed steps
  const completedSteps: number[] = [];
  for (let step = 1; step <= 3; step++) {
    if (isStepComplete(step, formData)) {
      completedSteps.push(step);
    }
  }

  // Render current step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <PromptInput
            value={formData.prompt}
            onChange={(value) => updateField('prompt', value)}
            onBlur={(value) => handleFieldBlur('prompt', value)}
            error={errors.prompt}
          />
        );

      case 2:
        return (
          <BrandSettings
            brandName={formData.brandName}
            brandLogo={formData.brandLogo}
            primaryColor={formData.brandColors.primary}
            secondaryColor={formData.brandColors.secondary}
            includeCta={formData.includeCta}
            ctaText={formData.ctaText}
            errors={errors}
            onBrandNameChange={(value) => updateField('brandName', value)}
            onBrandLogoChange={(logo) => updateField('brandLogo', logo)}
            onPrimaryColorChange={(color) => updateField('brandColors.primary', color)}
            onSecondaryColorChange={(color) => updateField('brandColors.secondary', color)}
            onIncludeCtaChange={(include) => updateField('includeCta', include)}
            onCtaTextChange={(text) => updateField('ctaText', text)}
            onFieldBlur={handleFieldBlur}
          />
        );

      case 3:
        return (
          <VideoParameters
            duration={formData.duration}
            aspectRatio={formData.aspectRatio}
            style={formData.style}
            musicStyle={formData.musicStyle}
            errors={errors}
            onDurationChange={(value) => updateField('duration', value)}
            onAspectRatioChange={(value) => updateField('aspectRatio', value)}
            onStyleChange={(value) => updateField('style', value)}
            onMusicStyleChange={(value) => updateField('musicStyle', value)}
          />
        );

      case 4:
        return (
          <ReviewStep
            formData={formData}
            onEdit={(step) => goToStep(step as 1 | 2 | 3 | 4)}
            isSubmitting={isSubmitting}
            submitError={submitError}
            onParallelizeChange={(checked) => updateField('parallelizeGenerations', checked)}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-full bg-background p-6 md:p-8 sm:p-4">
      <div className="max-w-[900px] mx-auto flex flex-col gap-6 lg:max-w-[900px] md:max-w-[720px]">
        <header className="text-center py-6 sm:py-4">
          <h1 className="text-3xl font-bold text-foreground mb-2 leading-tight sm:text-2xl">Create Ad Creative Video</h1>
          <p className="text-lg text-muted-foreground m-0 leading-normal sm:text-base">
            Generate a professional ad creative video in minutes with AI
          </p>
        </header>

        <StepIndicator
          currentStep={currentStep}
          completedSteps={completedSteps}
          onStepClick={(step) => goToStep(step as 1 | 2 | 3 | 4)}
        />

        <FormContainer
          currentStep={currentStep}
          onNext={nextStep}
          onPrevious={previousStep}
          onSubmit={submitForm}
          isSubmitting={isSubmitting}
          canGoNext={true}
        >
          {renderStepContent()}
        </FormContainer>
      </div>

      {/* Restore Draft Dialog */}
      <ConfirmDialog
        isOpen={showRestoreDialog}
        title="Previous Draft Found"
        message="A previous draft was found. Would you like to resume where you left off?"
        confirmLabel="Resume"
        cancelLabel="Discard"
        confirmVariant="primary"
        cancelVariant="outline"
        onConfirm={handleResume}
        onCancel={handleDiscard}
      />
    </div>
  );
};
