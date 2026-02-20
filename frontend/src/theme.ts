import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        brand: {
          50: { value: "#FFF9E6" },
          100: { value: "#FFF0BF" },
          200: { value: "#FFE699" },
          300: { value: "#FFDB66" },
          400: { value: "#FFD140" },
          500: { value: "#FFC72C" },
          600: { value: "#E6B327" },
          700: { value: "#CC9F22" },
          800: { value: "#997719" },
          900: { value: "#664F11" },
          950: { value: "#332808" },
        },
      },
    },
    semanticTokens: {
      colors: {
        brand: {
          solid: { value: "{colors.brand.500}" },
          contrast: { value: "#1A1A1A" },
          fg: { value: "{colors.brand.700}" },
          muted: { value: "{colors.brand.100}" },
          subtle: { value: "{colors.brand.50}" },
          emphasized: { value: "{colors.brand.600}" },
          focusRing: { value: "{colors.brand.500}" },
        },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
