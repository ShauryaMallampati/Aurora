# Citations & Acknowledgments

## Data Sources

### InterAgency Fire Perimeter History Database
- **Source**: U.S. Geological Survey (USGS) in partnership with state forestry agencies
- **Citation**: USGS (2024). "Fire Perimeters - All Years" - Historical fire perimeter data
- **URL**: https://www.usgs.gov/
- **Records**: 116,337 wildfires (1308-2024)
- **License**: Public domain (US government)
- **Usage**: Training scenarios, fire dynamics validation

### NOAA National Weather Service API
- **Source**: National Oceanic and Atmospheric Administration
- **Citation**: NOAA (2024). "National Weather Service Forecast API"
- **URL**: https://www.weather.gov/documentation/services-web-api
- **Data**: Temperature, wind speed, wind direction, humidity
- **License**: Public domain (US government)
- **Usage**: Weather integration for realistic fire simulation

### USGS 3DEP Elevation Data
- **Source**: USGS 3D Elevation Program
- **Citation**: USGS (2024). "3DEP - 3D Elevation Data"
- **URL**: https://www.usgs.gov/3dep
- **Data**: Digital elevation models, terrain analysis
- **License**: Public domain (US government)
- **Usage**: Terrain effects on fire spread modeling

---

## Research & Methodologies

### Reinforcement Learning Framework
- **PPO (Proximal Policy Optimization)**
  - Original paper: Schulman et al. (2017) "Proximal Policy Optimization Algorithms"
  - Implementation: Stable-Baselines3
  - Citation: Raffin et al. (2021)

### Large Language Models
- **Qwen 2.5 Models**
  - Source: Alibaba Qwen Team (2024)
  - Models: Qwen 2.5-1.5B, Qwen 2.5-3B, Qwen 2.5-7B
  - License: Apache 2.0
  - URL: https://huggingface.co/Qwen
  - Usage: Strategic guidance layer

---

## Software Libraries & Frameworks

### Machine Learning & RL
- **Stable-Baselines3** (Raffin et al., 2021)
  - License: MIT
  - GitHub: https://github.com/DLR-RM/stable-baselines3
  - Usage: PPO implementation, model training

- **Gymnasium** (formerly OpenAI Gym)
  - License: MIT
  - GitHub: https://github.com/Farama-Foundation/Gymnasium
  - Usage: RL environment interface

- **PyTorch** (Paszke et al., 2019)
  - License: BSD
  - URL: https://pytorch.org/
  - Usage: Deep learning framework

- **Transformers** (Wolf et al., 2020)
  - License: Apache 2.0
  - GitHub: https://github.com/huggingface/transformers
  - Usage: LLM inference, tokenization

### Geospatial & Data
- **GeoPandas** (Jordahl et al., 2021)
  - License: BSD
  - GitHub: https://github.com/geopandas/geopandas
  - Usage: Shapefile processing, fire perimeter handling

- **Rasterio** (Toblerity Contributors)
  - License: BSD
  - GitHub: https://github.com/rasterio/rasterio
  - Usage: Elevation data processing

- **Shapely** (Gillies et al.)
  - License: BSD
  - GitHub: https://github.com/shapely/shapely
  - Usage: Geometric operations

- **Pandas** (McKinney, 2010)
  - License: BSD
  - URL: https://pandas.pydata.org/
  - Usage: Data manipulation, metrics tracking

- **NumPy** (Harris et al., 2020)
  - License: BSD
  - URL: https://numpy.org/
  - Usage: Numerical computations

### Visualization & Web
- **Matplotlib** (Hunter, 2007)
  - License: PSF
  - URL: https://matplotlib.org/
  - Usage: Evaluation plots, visualization

- **Seaborn** (Waskom, 2021)
  - License: BSD
  - URL: https://seaborn.pydata.org/
  - Usage: Statistical visualizations

- **Next.js** (Vercel)
  - License: MIT
  - URL: https://nextjs.org/
  - Usage: Web dashboard frontend

- **Recharts**
  - License: MIT
  - GitHub: https://github.com/recharts/recharts
  - Usage: Interactive charts and visualization

- **Tailwind CSS** (Tailwind Labs)
  - License: MIT
  - URL: https://tailwindcss.com/
  - Usage: CSS styling framework

---

## Research Papers Referenced

1. **Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O.** (2017)
   - "Proximal Policy Optimization Algorithms"
   - Paper: https://arxiv.org/abs/1707.06347

2. **Raffin, A., Hill, A., Ernestus, M., Gleich, A., Kanervisto, A., & Dormann, N.** (2021)
   - "Stable-Baselines3: Reliable Reinforcement Learning Implementations"
   - Paper: https://jmlr.org/papers/v22/20-1364.html

3. **Wolf, T., Debut, L., Sanh, V., et al.** (2020)
   - "HuggingFace's Transformers: State-of-the-art Natural Language Processing"
   - Paper: https://arxiv.org/abs/1910.03771

4. **Paszke, A., Gross, S., Massa, F., et al.** (2019)
   - "PyTorch: An Imperative Style, High-Performance Deep Learning Library"
   - Paper: https://arxiv.org/abs/1912.01703

5. **Harris, C. R., Millman, K. J., van der Walt, S. J., et al.** (2020)
   - "Array programming with NumPy"
   - Paper: https://doi.org/10.1038/s41586-020-2649-2

6. **McKinney, W.** (2010)
   - "Data Structures for Statistical Computing in Python"
   - Proceedings of the 9th Python in Science Conference

7. **Hunter, J. D.** (2007)
   - "Matplotlib: A 2D Graphics Environment"
   - Computing in Science & Engineering, 9(3), 90-95

---

## Methodological References

### Fire Dynamics & Wildfire Management
- **Finney, M. A.** (2004) "FARSITE: Fire Area Simulator - model development and evaluation"
  - Used as reference for fire spread physics

- **National Fire Protection Association (NFPA)**
  - Fire department response time data and standards

- **CAL FIRE (California Department of Forestry and Fire Protection)**
  - Wildfire behavior data, response protocols, historical case studies

- **USGS FireCape Project**
  - Fire spread modeling, terrain effects documentation

---

## Contributors

- **Shaurya Mallampati** - Project lead, hybrid architecture design, training pipeline
- **AURORA Development Team** - Code implementation, testing, evaluation

---

## How to Cite AURORA

### BibTeX
```bibtex
@software{aurora2025,
  title={AURORA: Hybrid LLM-Guided RL for Autonomous Wildfire Containment},
  author={Mallampati, Shaurya},
  year={2025},
  url={https://github.com/yourusername/AURORA},
  license={MIT}
}
```

### APA
Mallampati, S. (2025). AURORA: Hybrid LLM-Guided RL for Autonomous Wildfire Containment [Software]. Retrieved from https://github.com/yourusername/AURORA

### MLA
Mallampati, Shaurya. "AURORA: Hybrid LLM-Guided RL for Autonomous Wildfire Containment." GitHub, 2025, github.com/yourusername/AURORA.

---

## Third-Party Licenses

All dependencies are compatible with the MIT license. Full license texts available:
- Stable-Baselines3: https://github.com/DLR-RM/stable-baselines3/blob/master/LICENSE
- PyTorch: https://github.com/pytorch/pytorch/blob/master/LICENSE
- Transformers: https://github.com/huggingface/transformers/blob/main/LICENSE
- GeoPandas: https://github.com/geopandas/geopandas/blob/main/LICENSE.txt

---

## Acknowledgments

- U.S. Geological Survey (USGS) for fire perimeter data
- NOAA for weather integration
- Alibaba Qwen team for open-source LLMs
- Hugging Face community for transformers library
- Stable-Baselines3 team for robust RL implementations
- ISEF organizers for competition opportunity
- All open-source contributors to libraries used

