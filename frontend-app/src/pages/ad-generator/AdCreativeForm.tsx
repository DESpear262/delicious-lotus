import React from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Sparkles } from 'lucide-react';

export const AdCreativeForm: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentStep,
    formData,
    errors,
    isSubmitting,
    submitError,
    analysisResult,
    promptResult,
    promptError,
    isGeneratingPrompts,
    updateField,
    handleFieldBlur,
    nextStep,
    previousStep,
    goToStep,
    submitForm,
    generatePrompts,
    showRestoreDialog,
    handleResume,
    handleDiscard,
  } = useGenerationForm();

  const renderJsonBlock = (data: unknown) => {
    if (!data) return <p className="text-sm text-muted-foreground">No data returned.</p>;
    return (
      <pre className="rounded-lg bg-muted/60 p-4 text-xs text-foreground overflow-x-auto border border-border">
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  };

  // Calculate completed steps
  // Calculate completed steps
  const completedSteps: number[] = [];
  // Step 1: Prompt
  if (isStepComplete(1, formData)) completedSteps.push(1);
  // Step 2: Video Params (was 3)
  if (isStepComplete(3, formData)) completedSteps.push(2);
  // Step 3: Review (was 4)
  if (isStepComplete(4, formData)) completedSteps.push(3);
  // Step 4: Results
  if (promptResult) completedSteps.push(4);

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

      // Case 2 (Brand) is skipped/hidden

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
            promptResult={promptResult} // Pass promptResult to show "View Results" button if needed inside component
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background pb-12">
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <header className="text-center mb-8">
          <div className="inline-flex items-center gap-2 text-primary mb-3">
            <Sparkles className="h-5 w-5" />
            <span className="text-sm font-medium uppercase tracking-wider">AI Video Generator</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Create Ad Creative Video
          </h1>
          <p className="mt-2 text-muted-foreground">
            Generate a professional ad creative video in minutes with AI
          </p>
        </header>

        {/* Stepper */}
        <div className="mb-8">
          <StepIndicator
            currentStep={promptResult ? 4 : (currentStep === 1 ? 1 : currentStep === 3 ? 2 : 3)}
            completedSteps={completedSteps}
            steps={[
              { id: 1, title: 'Prompt', description: 'Describe your video' },
              { id: 2, title: 'Video Settings', description: 'Duration & Style' },
              { id: 3, title: 'Review', description: 'Final Check' },
              { id: 4, title: 'Results', description: 'View Prompts' }
            ]}
            onStepClick={(step) => {
              // Map visual step back to internal step
              const internalStep = step === 1 ? 1 : step === 2 ? 3 : 4;

              // Handle Results step click
              if (step === 4) {
                if (promptResult) {
                  navigate('/ad-generator/prompt-results');
                }
                return;
              }

              // Allow navigation if step is completed OR if we have results (flow done)
              const isFlowComplete = !!promptResult;
              const targetIsCompleted = completedSteps.includes(step); // visual step check

              if (isFlowComplete || targetIsCompleted || internalStep < currentStep) {
                goToStep(internalStep as 1 | 3 | 4);
              }
            }}
          />
        </div>

        {/* Form Content */}
        <FormContainer
          currentStep={currentStep}
          onNext={nextStep}
          onPrevious={previousStep}
          onSubmit={submitForm}
          isSubmitting={isSubmitting}
          canGoNext={true}
          onGeneratePrompts={generatePrompts}
          isGeneratingPrompts={isGeneratingPrompts}
          generateButtonLabel={promptResult ? "View Results" : "Generate Prompts"}
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

      {(analysisResult || promptResult || promptError) && (
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 mt-8">
          <div className="bg-card border border-primary/30 rounded-xl shadow-sm p-6 space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="inline-flex items-center gap-2 text-primary mb-2">
                  <Sparkles className="h-4 w-4" />
                  <span className="text-xs font-semibold uppercase tracking-wide">Analysis Output</span>
                </div>
                <h3 className="text-xl font-semibold text-foreground">We analyzed your request</h3>
                <p className="text-sm text-muted-foreground">
                  Prompt analysis, brand insights, scene breakdown, and generated micro-prompts are returned below.
                </p>
              </div>
              {analysisResult?.generation_id && (
                <div className="text-right">
                  <p className="text-xs uppercase text-muted-foreground">Generation ID</p>
                  <p className="font-mono text-sm text-foreground">{analysisResult.generation_id}</p>
                </div>
              )}
            </div>

            {analysisResult && (
              <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
                <div className="rounded-lg border border-border bg-muted/40 p-3">
                  <p className="text-xs text-muted-foreground">Scenes</p>
                  <p className="text-lg font-semibold text-foreground">{analysisResult.scenes?.length ?? 0}</p>
                </div>
                <div className="rounded-lg border border-border bg-muted/40 p-3">
                  <p className="text-xs text-muted-foreground">Micro-prompts</p>
                  <p className="text-lg font-semibold text-foreground">{analysisResult.micro_prompts?.length ?? 0}</p>
                </div>
                <div className="rounded-lg border border-border bg-muted/40 p-3">
                  <p className="text-xs text-muted-foreground">Brand Config</p>
                  <p className="text-lg font-semibold text-foreground">
                    {analysisResult.brand_config ? 'Returned' : 'None'}
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-muted/40 p-3">
                  <p className="text-xs text-muted-foreground">Status</p>
                  <p className="text-lg font-semibold text-foreground capitalize">{analysisResult.status}</p>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {analysisResult && (
                <>
                  <div>
                    <p className="text-sm font-semibold text-foreground mb-1">Prompt Analysis</p>
                    {renderJsonBlock(analysisResult.prompt_analysis)}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground mb-1">Brand Analysis</p>
                    {renderJsonBlock(analysisResult.brand_config)}
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <div>
                      <p className="text-sm font-semibold text-foreground mb-1">Scene Decomposition</p>
                      {renderJsonBlock(analysisResult.scenes)}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-foreground mb-1">Micro-prompts</p>
                      {renderJsonBlock(analysisResult.micro_prompts)}
                    </div>
                  </div>
                </>
              )}

              {promptResult && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-semibold text-foreground">Clip Prompts (OpenAI)</p>
                    <p className="text-xs text-muted-foreground">
                      {promptResult.content?.length ?? 0} clips
                    </p>
                  </div>
                  {renderJsonBlock(promptResult)}
                </div>
              )}

              {promptError && (
                <div className="flex items-center gap-3 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                  <span className="text-sm text-destructive">{promptError}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
