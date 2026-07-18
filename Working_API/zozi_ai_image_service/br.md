Based on the code and rembg library, here's a comprehensive list of **all available models, variants, and detection techniques**:

---

## **📦 Available Models in rembg**

### **1. BiRefNet Variants** (Best Quality)

| Model | Usage | Best For | Memory | Speed |
|-------|-------|----------|--------|-------|
| `birefnet-general` | General purpose | High-quality products | Very High | Slow |
| `birefnet-general-lite` | Lightweight | Standard e-commerce | Medium | Medium |
| `birefnet-massive` | Maximum accuracy | Complex scenes | Very High | Very Slow |
| `birefnet-hrsod` | High-Resolution SOD | Detailed products | High | Slow |
| `birefnet-portrait` | Portrait mode | Humans/faces | High | Medium |
| `birefnet-dis` | Dichotomous segmentation | Binary masks | High | Medium |

### **2. ISNet Variants** (Fast & Reliable)

| Model | Usage | Best For | Memory | Speed |
|-------|-------|----------|--------|-------|
| `isnet-general-use` | **General purpose** | **E-commerce products** ⭐ | Low | **Fast** |
| `isnet-anime` | Anime/cartoon | Manga, illustrations | Low | Fast |

### **3. U²Net Variants** (Balanced)

| Model | Usage | Best For | Memory | Speed |
|-------|-------|----------|--------|-------|
| `u2net` | General purpose | Standard products | Medium | Medium |
| `u2netp` | Lightweight | Mobile/low-resource | Low | Fast |
| `u2net_cloth_seg` | **Clothing segmentation** | **Bikinis, apparel** 👕 | Medium | Medium |

### **4. Other Models**

| Model | Usage | Best For | Memory | Speed |
|-------|-------|----------|--------|-------|
| `silueta` | Body segmentation | Humans, animals | Low | Fast |
| `briaai-rmbg-1.4` | **Industry standard** | **Complex marketing images** 🎨 | Medium | **Fast** |
| `sam2` | Segment Anything 2 | Complex scenes | Very High | Slow |
| `vitmatte` | Neural matting | Hair, fur, fine details | High | Medium |

---

## **🔍 Detection Techniques (From Code)**

### **Color Space Analysis**

1. **RGB** - Standard color space
2. **HSV** - Hue, Saturation, Value (for skin detection)
3. **LAB** - Lightness, a, b channels (for wood/background detection)
4. **YCrCb** - Luma, chroma (for skin detection)

### **Edge & Texture Detection**

5. **Canny Edge Detection** - Edge density analysis
6. **Laplacian Variance** - Texture complexity
7. **Gaussian Blur** - Noise reduction
8. **Sobel Operators** - Gradient detection

### **Morphological Operations**

9. **Erosion** - Shrink objects
10. **Dilation** - Expand objects
11. **Opening** - Remove small noise
12. **Closing** - Fill small holes
13. **Distance Transform** - Distance from edges

### **Contour Analysis**

14. **Connected Components** - Find separate objects
15. **Contour Area** - Size measurement
16. **Bounding Box** - Aspect ratio
17. **Circularity** - Shape analysis
18. **Convex Hull** - Shape filling

### **Color Analysis**

19. **K-Means Clustering** - Dominant color detection
20. **Color Distance** - Euclidean distance in RGB/LAB
21. **Brightness/Contrast** - Exposure analysis
22. **Saturation** - Color richness
23. **Color Balance** - RGB channel balance

### **Skin Detection**

24. **HSV Skin Ranges** - Multiple skin tone detection
25. **YCrCb Skin Detection** - Alternative skin detection

### **Advanced Techniques**

26. **CLAHE** - Contrast Limited Adaptive Histogram Equalization
27. **Bilateral Filter** - Edge-preserving smoothing
28. **Guided Filter** - Edge-aware filtering
29. **Alpha Matting** - Fine edge refinement
30. **Neural Matting** - ViTMatte for hair/fur

---

## **📊 Subject Detection Metrics (From Code)**

The `SubjectDetector` class uses these metrics:

| Metric | Purpose | Threshold |
|--------|---------|-----------|
| `skin_ratio` | Detect humans/clothing | >0.15 = human |
| `hair_edge_density` | Detect hair | >0.15 = hair |
| `edge_density` | Detect complexity | >0.2 = complex |
| `texture_complexity` | Detect food/texture | >1000 = food |
| `aspect_ratio` | Detect furniture | >1.5 or <0.67 |
| `circularity` | Detect products | >0.8 = product |
| `edge_contrast` | Detect transparent | <30 = transparent |
| `color_variance` | Detect complexity | High = complex |
| `coverage` | Detect minimal | <0.05 = minimal |

---

## **🎯 Recommended Model Priority for E-Commerce**

```python
models_to_try = [
    'briaai-rmbg-1.4',        # 1st: Best for complex scenes
    'birefnet-general-lite',  # 2nd: Good balance
    'u2net_cloth_seg',        # 3rd: Best for bikinis/clothing
    'isnet-general-use',      # 4th: Reliable fallback
    'silueta',                # 5th: For humans
]
```

---

## **📋 Complete Feature List**

### **Pre-processing**
- CLAHE contrast enhancement
- LAB color space conversion
- Image resizing
- Quality analysis

### **Segmentation**
- Multi-model ensemble
- Probability map fusion
- Confidence estimation
- Adaptive thresholds

### **Post-processing**
- Edge refinement
- Hole filling
- Background cleanup
- Color decontamination
- Halo removal
- Shadow removal
- Reflection preservation

### **Quality Control**
- Coverage scoring
- Edge quality scoring
- Halo detection
- Background uniformity
- Artifact detection
- Color spill detection

---

This is the **complete list** of all detection techniques, models, and variants available in your codebase and rembg library!