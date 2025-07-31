# Flow Matching for Image Generation - References and Further Reading

## Core Papers

### Foundational Work
1. **Flow Matching for Generative Modeling**
   - Authors: Yaron Lipman, Ricky T. Q. Chen, Heli Ben-Hamu, Maximilian Nickel, Matt Le
   - arXiv: 2210.02747 (2022)
   - URL: https://arxiv.org/abs/2210.02747
   - **Key Contribution**: Introduces Flow Matching as a simulation-free method for training CNFs

2. **Rectified Flow: A Marginal Preserving Approach to Optimal Transport**
   - Authors: Xingchao Liu, Chengyue Gong, Qiang Liu
   - arXiv: 2209.14577 (2022)
   - **Key Contribution**: Introduces rectified flows with straight-line probability paths

### Background Papers

3. **Neural Ordinary Differential Equations**
   - Authors: Ricky T. Q. Chen, Yulia Rubanova, Jesse Bettencourt, David Duvenaud
   - NeurIPS 2018
   - **Key Contribution**: Introduces Neural ODEs, foundation for continuous normalizing flows

4. **FFJORD: Free-form Continuous Dynamics for Scalable Reversible Generative Models**
   - Authors: Will Grathwohl, Ricky T. Q. Chen, Jesse Bettencourt, Ilya Sutskever, David Duvenaud
   - ICLR 2019
   - **Key Contribution**: Scalable continuous normalizing flows

## Applications in Image Generation

### Stable Diffusion 3
5. **Scaling Rectified Flow Transformers for High-Resolution Image Synthesis**
   - Stability AI Technical Report (2024)
   - **Key Contribution**: Application of Flow Matching in production text-to-image systems

### Other Applications
6. **Flux Models**
   - Black Forest Labs
   - **Key Contribution**: Practical implementation of rectified flows for image generation

## Theoretical Background

### Normalizing Flows
7. **Normalizing Flows for Probabilistic Modeling and Inference**
   - Authors: George Papamakarios, Eric Nalisnick, Danilo Jimenez Rezende, Shakir Mohamed, Balaji Lakshminarayanan
   - Journal of Machine Learning Research (2021)
   - **Key Contribution**: Comprehensive survey of normalizing flows

### Optimal Transport
8. **Computational Optimal Transport**
   - Authors: Gabriel Peyré, Marco Cuturi
   - Foundations and Trends in Machine Learning (2019)
   - **Key Contribution**: Mathematical foundations of optimal transport

## Comparison with Other Generative Models

### Diffusion Models
9. **Denoising Diffusion Probabilistic Models**
   - Authors: Jonathan Ho, Ajay Jain, Pieter Abbeel
   - NeurIPS 2020
   - **Key Contribution**: Foundation of modern diffusion models

10. **Score-Based Generative Modeling through Stochastic Differential Equations**
    - Authors: Yang Song, Jascha Sohl-Dickstein, Diederik P. Kingma, Abhishek Kumar, Stefano Ermon, Ben Poole
    - ICLR 2021
    - **Key Contribution**: Unified view of score-based models and diffusion models

## Implementation Resources

### Official Implementations
- **Flow Matching GitHub Repository**: https://github.com/facebookresearch/flow_matching
- **Rectified Flow Implementation**: https://github.com/gnobitab/RectifiedFlow

### Tutorial Materials
- **Flow Matching Tutorial Notebooks**: Available on the official repository
- **NeurIPS 2024 Tutorial**: "Flow Matching for Generative Modeling"

## Mathematical Background

### Probability Theory
11. **Probability Theory: The Logic of Science**
    - Author: E.T. Jaynes
    - Cambridge University Press (2003)
    - **Relevance**: Foundation for understanding probability paths

### Differential Equations
12. **Ordinary Differential Equations**
    - Author: Morris Tenenbaum, Harry Pollard
    - Dover Publications
    - **Relevance**: Understanding ODE solving for sampling

## Recent Developments and Extensions

### Stochastic Interpolants
13. **Stochastic Interpolants: A Unifying Framework for Flows and Diffusions**
    - Authors: Michael S. Albergo, Nicholas M. Boffi, Eric Vanden-Eijnden
    - arXiv: 2303.08797 (2023)
    - **Key Contribution**: Generalizes Flow Matching to stochastic processes

### Conditional Generation
14. **Flow Matching for Conditional Generation**
    - Various recent papers exploring conditioning mechanisms
    - **Key Contribution**: Extensions for controllable generation

## Blogs and Explanatory Materials

### Technical Blogs
- **Lil'Log**: "Flow-based Deep Generative Models" by Lilian Weng
- **Distill.pub**: Various articles on generative modeling
- **Papers With Code**: Flow Matching implementations and benchmarks

### Video Lectures
- **NeurIPS 2024 Tutorial**: Flow Matching for Generative Modeling
- **ICML Workshops**: Various talks on continuous normalizing flows
- **YouTube**: Academic presentations by paper authors

## Datasets and Benchmarks

### Standard Benchmarks
- **CIFAR-10/100**: Standard image generation benchmarks
- **CelebA-HQ**: High-resolution face generation
- **ImageNet**: Large-scale natural image generation

### Evaluation Metrics
- **FID (Fréchet Inception Distance)**: Standard quality metric
- **IS (Inception Score)**: Diversity and quality measure
- **Sampling Speed**: Function evaluations needed for generation

## Software and Tools

### Deep Learning Frameworks
- **PyTorch**: Primary framework for most implementations
- **JAX**: Alternative for research implementations
- **TensorFlow**: Some implementations available

### ODE Solvers
- **torchdiffeq**: PyTorch-based ODE solvers
- **diffrax**: JAX-based differential equation library
- **scipy.integrate**: Standard numerical integration

## Future Research Directions

### Open Problems
1. **Architecture Design**: Better neural network architectures for vector fields
2. **Sampling Efficiency**: Reducing the number of function evaluations needed
3. **Theoretical Understanding**: Deeper analysis of different probability paths
4. **Scalability**: Scaling to very high-resolution generation
5. **Multi-modal Applications**: Extension to video, 3D, and other modalities

### Emerging Areas
- **Flow Matching + Transformers**: Integration with modern architectures
- **Discrete Flow Matching**: Extensions to discrete data
- **Federated Flow Matching**: Distributed training approaches
- **Quantum Flow Matching**: Quantum computing applications

## Citation Format

When citing Flow Matching in academic work:

```bibtex
@article{lipman2022flow,
  title={Flow Matching for Generative Modeling},
  author={Lipman, Yaron and Chen, Ricky T. Q. and Ben-Hamu, Heli and Nickel, Maximilian and Le, Matt},
  journal={arXiv preprint arXiv:2210.02747},
  year={2022}
}
```

## Additional Learning Resources

### Online Courses
- **CS236 (Stanford)**: Deep Generative Models
- **CS294 (Berkeley)**: Deep Unsupervised Learning
- **Various Coursera/edX**: Machine Learning specializations

### Books
- **Deep Learning** by Ian Goodfellow, Yoshua Bengio, Aaron Courville
- **Pattern Recognition and Machine Learning** by Christopher Bishop
- **The Elements of Statistical Learning** by Hastie, Tibshirani, Friedman

### Research Groups
- **Facebook AI Research (FAIR)**: Original Flow Matching development
- **Google Research**: Continuous normalizing flows research
- **Stability AI**: Practical applications in image generation
- **Black Forest Labs**: Advanced flow-based models

This comprehensive reference list provides students and researchers with the necessary resources to deepen their understanding of Flow Matching and its applications in image generation, from foundational theory to cutting-edge applications.