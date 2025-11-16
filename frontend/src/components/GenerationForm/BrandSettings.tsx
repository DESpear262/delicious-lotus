import React from 'react';
import { Input } from '@/components/ui/Input';
import { ColorPicker } from '@/components/ui/ColorPicker';
import { Radio } from '@/components/ui/Radio';
import { AssetUploader, type UploadedAsset } from '@/components/AssetUploader';
import styles from './BrandSettings.module.css';

interface BrandSettingsProps {
  brandName: string;
  brandLogo: UploadedAsset | null;
  primaryColor: string;
  secondaryColor: string;
  includeCta: boolean;
  ctaText: string;
  errors: Record<string, string>;
  onBrandNameChange: (value: string) => void;
  onBrandLogoChange: (logo: UploadedAsset | null) => void;
  onPrimaryColorChange: (color: string) => void;
  onSecondaryColorChange: (color: string) => void;
  onIncludeCtaChange: (include: boolean) => void;
  onCtaTextChange: (text: string) => void;
  onFieldBlur: (field: string, value: any) => void;
}

export const BrandSettings: React.FC<BrandSettingsProps> = ({
  brandName,
  brandLogo,
  primaryColor,
  secondaryColor,
  includeCta,
  ctaText,
  errors,
  onBrandNameChange,
  onBrandLogoChange,
  onPrimaryColorChange,
  onSecondaryColorChange,
  onIncludeCtaChange,
  onCtaTextChange,
  onFieldBlur,
}) => {
  const handleLogoUpload = (assets: UploadedAsset[]) => {
    if (assets.length > 0) {
      onBrandLogoChange(assets[0]);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Brand Identity</h2>
        <p className={styles.description}>
          Configure your brand settings to ensure visual consistency throughout the video.
        </p>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Basic Information</h3>
        <Input
          label="Brand Name (Optional)"
          value={brandName}
          onChange={(e) => onBrandNameChange(e.target.value)}
          onBlur={(e) => onFieldBlur('brandName', e.target.value)}
          error={errors.brandName}
          placeholder="e.g., Acme Corporation"
          helperText="Your brand name will appear in the video if provided"
          fullWidth
        />
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Brand Logo</h3>
        <p className={styles.sectionDescription}>
          Upload your logo to include it in the video (optional)
        </p>
        <AssetUploader
          accept="image/*"
          maxSize={50 * 1024 * 1024}
          maxFiles={1}
          onUploadComplete={handleLogoUpload}
          existingAssets={brandLogo ? [brandLogo] : []}
        />
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Brand Colors</h3>
        <p className={styles.sectionDescription}>
          Choose colors that represent your brand
        </p>
        <div className={styles.colorGrid}>
          <ColorPicker
            label="Primary Color"
            value={primaryColor}
            onChange={onPrimaryColorChange}
            error={errors['brandColors.primary']}
            fullWidth
          />
          <ColorPicker
            label="Secondary Color"
            value={secondaryColor}
            onChange={onSecondaryColorChange}
            error={errors['brandColors.secondary']}
            fullWidth
          />
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Call-to-Action</h3>
        <p className={styles.sectionDescription}>
          Add a call-to-action at the end of your video
        </p>
        <Radio
          options={[
            {
              value: 'yes',
              label: 'Include CTA',
              description: 'Add a call-to-action message at the end',
            },
            {
              value: 'no',
              label: 'No CTA',
              description: 'End without a call-to-action',
            },
          ]}
          value={includeCta ? 'yes' : 'no'}
          onChange={(value) => onIncludeCtaChange(value === 'yes')}
          name="includeCta"
          orientation="horizontal"
        />

        {includeCta && (
          <div className={styles.ctaInput}>
            <Input
              label="CTA Text"
              value={ctaText}
              onChange={(e) => onCtaTextChange(e.target.value)}
              onBlur={(e) => onFieldBlur('ctaText', e.target.value)}
              error={errors.ctaText}
              placeholder="e.g., Visit our website, Learn more, Shop now"
              helperText="Keep it short and actionable (max 50 characters)"
              maxLength={50}
              fullWidth
            />
          </div>
        )}
      </div>

      <div className={styles.infoBox}>
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={styles.infoIcon}
        >
          <path
            d="M10 0C4.477 0 0 4.477 0 10s4.477 10 10 10 10-4.477 10-10S15.523 0 10 0zm1 15H9v-6h2v6zm0-8H9V5h2v2z"
            fill="currentColor"
          />
        </svg>
        <p className={styles.infoText}>
          Brand settings are optional but help create a more personalized and consistent video that aligns with your brand identity.
        </p>
      </div>
    </div>
  );
};
