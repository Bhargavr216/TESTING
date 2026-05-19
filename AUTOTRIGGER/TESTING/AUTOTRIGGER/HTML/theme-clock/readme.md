
<div align="left">
**UNIT – I**

**QUESTION 1: What is Machine Learning? Explain its importance and role in modern computing.**

**Definition:** Machine Learning (ML) is a branch of AI that enables computers to learn patterns from data and make decisions without being explicitly programmed. It improves performance automatically through experience.

**Role in Modern Computing:** It transforms systems into smart, data-driven applications capable of automation and real-time predictions.

**Diagram:**
```
          Training Data
               |
               v
        Machine Learning
             Algorithm
               |
               v
             Model
               |
               v
        Predictions / Decisions
```

**Importance:**
1. **Handles Big Data:** Analyzes huge datasets faster than humans.
2. **Automation:** Reduces human effort in decision-making.
3. **Adaptability:** Learns and improves with new data.
4. **Solves Complex Problems:** Tackles issues like image recognition where rules are unknown.

---

**QUESTION 2: Describe the different types of learning in Machine Learning.**

**Definition:** Machine Learning is classified into four types based on the nature of data and feedback mechanism: Supervised, Unsupervised, Semi-supervised, and Reinforcement Learning.

**Types & Concepts:**

1. **Supervised Learning:**
   - **What is it:** Learning with labeled input-output pairs.
   - **Examples:** Spam detection, Linear Regression.
2. **Unsupervised Learning:**
   - **What is it:** Finding hidden patterns in unlabeled data.
   - **Examples:** Clustering (K-Means), PCA.
3. **Semi-Supervised Learning:**
   - **What is it:** Uses a small amount of labeled data with large unlabeled data.
   - **Examples:** Speech recognition.
4. **Reinforcement Learning:**
   - **What is it:** Learning through trial and error via rewards/penalties.
   - **Examples:** Q-Learning, Game playing.

**Comparison Table:**
| Type | Labeled Data | Feedback | Example |
|------|-------------|----------|---------|
| Supervised | Yes | Direct | Spam detection |
| Unsupervised | No | None | Customer clustering |
| Semi-Supervised | Small/Partial | Partial | Web classification |
| Reinforcement | No | Rewards | Robotics |

---

**QUESTION 3: Explain real-world applications of Machine Learning.**

**Definition:** ML is widely used across industries to automate tasks, analyze data, and predict outcomes by learning from historical patterns.

**Applications by Domain:**

1. **Healthcare:** Disease prediction and medical image analysis.
2. **Finance:** Credit scoring, fraud detection, and algorithmic trading.
3. **E-Commerce:** Product recommendation systems.
4. **Transportation:** Self-driving cars and traffic prediction.
5. **Social Media:** Face recognition and content filtering.
6. **Education:** Personalized learning platforms.

---

**QUESTION 4: What is supervised learning? Explain how learning a class from examples works.**

**Definition:** Supervised learning is a type of ML where the model learns a mapping function from input features to known output labels using labeled training data.

**How Learning Works:**
- **Step 1:** Data Collection with known labels.
- **Step 2:** Feature Extraction (converting data to numbers).
- **Step 3:** Model Training (finding patterns).
- **Step 4:** Prediction (using patterns on new data).

**Diagram:**
```
   Labeled Data (X, Y)
          |
          v
   Supervised Algorithm
          |
          v
        Learned Model
          |
          v
   Predicted Class / Value
```

---

**QUESTION 5: Compare learning multiple classes and binary classification.**

**Definition:** Binary classification involves predicting one of two classes, while multi-class classification involves predicting one of three or more classes.

**Binary Classification:**
- **What is it:** Output is 0 or 1 (Yes/No).
- **Example:** Spam detection.

**Multi-Class Classification:**
- **What is it:** Output belongs to Class 1, 2, 3... etc.
- **Example:** Digit recognition (0-9).

**Comparison Table:**
| Aspect | Binary | Multi-Class |
|--------|--------|------------|
| Classes | Two | More than two |
| Complexity | Low | High |
| Algorithms | Logistic Regression | Neural Networks |

---

**QUESTION 6: What is regression in Machine Learning? How does it differ from classification?**

**Definition:** Regression is a supervised learning technique used to predict continuous numerical values, whereas classification predicts categorical class labels.

**Regression:**
- **Output:** Continuous values (e.g., Price, Temperature).
- **Formula:** $y = mx + c$

**Classification:**
- **Output:** Discrete categories (e.g., Spam/Not Spam).
- **Formula:** Thresholding probability.

**Comparison Table:**
| Aspect | Regression | Classification |
|--------|------------|----------------|
| Output | Continuous | Discrete/Categorical |
| Nature | Numerical | Categorical |
| Example | House Price | Disease Prediction |

---

**QUESTION 7: Explain Linear Regression and describe situations where it is applied.**

**Definition:** Linear Regression models the relationship between a dependent variable and one independent variable using a straight line (best fit line).

**Equation (Compulsory):**
$$y = mx + c$$
*(Where y=output, x=input, m=slope, c=intercept)*

**Assumptions:**
1. Linear relationship.
2. Independence of errors.
3. Homoscedasticity (constant variance).

**Diagram:**
```
y
│          ●
│       ●
│    ●
│ ●
│________________ x
      Best Fit Line
```

**Applications:** House price prediction, Sales forecasting, Salary estimation.

---

**QUESTION 8: What is Multiple Linear Regression? How does it extend Simple Linear Regression?**

**Definition:** Multiple Linear Regression predicts a dependent variable using two or more independent variables by fitting a hyperplane.

**Equation (Compulsory):**
$$y = b_0 + b_1x_1 + b_2x_2 + ... + b_nx_n$$

**Extension:**
- **Simple:** One input feature (Line).
- **Multiple:** Multiple input features (Hyperplane).

**Diagram:**
```
x1 ──┐
     │
x2 ──┼──► MLR Model ──► y
     │
x3 ──┘
```

---

**QUESTION 9: Describe Logistic Regression. With a suitable example explain its use in classification.**

**Definition:** Logistic Regression is a classification algorithm that predicts the probability of a binary outcome (0 or 1) using the Sigmoid function.

**Sigmoid Function (Compulsory):**
$$\sigma(z) = \frac{1}{1 + e^{-z}}$$
*(Maps output between 0 and 1)*

**Diagram (S-Curve):**
```
Probability
 1 |        _______
   |      /
   |    /
 0.5|---●------------
   |  /
   |/
 0 |___________________
        Input (z)
```

**Example:** Email Spam Classification (Output > 0.5 is Spam).

---

**UNIT – II**

**QUESTION 1: Describe and explain the different types of problems solved using ML.**

**Definition:** ML solves problems ranging from predicting values to identifying patterns and making sequential decisions.

**Problem Types:**
1. **Classification:** Assigning categories (e.g., Spam detection).
2. **Regression:** Predicting continuous values (e.g., Stock prices).
3. **Clustering:** Grouping similar data (e.g., Customer segmentation).
4. **Dimensionality Reduction:** Reducing features (e.g., PCA).
5. **Anomaly Detection:** Finding outliers (e.g., Fraud).

---

**QUESTION 2: How does a Logistic Model differ from a Linear Regression Model?**

**Definition:** Logistic Regression is for classification (probability output), while Linear Regression is for regression (continuous output).

**Differences:**
- **Linear:** Output ranges from -∞ to +∞. Uses Mean Squared Error.
- **Logistic:** Output ranges from 0 to 1. Uses Log Loss.

---

**QUESTION 3: Discuss the importance of selecting relevant and meaningful features.**

**Definition:** Feature selection is the process of choosing the most relevant variables to improve model performance and reduce complexity.

**Importance:**
1. **Improves Accuracy:** Removes noise.
2. **Reduces Overfitting:** Simplifies the model.
3. **Faster Training:** Less computational cost.
4. **Better Interpretability:** Easier to understand.

---

**QUESTION 4: What is feature construction and feature transformation?**

**Definition:** Creating new features from existing ones is Feature Construction; modifying existing features is Feature Transformation.

**Feature Construction:** Creating "BMI" from Height and Weight.
**Feature Transformation:** Scaling data to 0-1 range (Normalization).

**Difference Table:**
| Aspect | Construction | Transformation |
|--------|--------------|----------------|
| New Features | Yes | No |
| Example | BMI | Normalization |

---

**QUESTION 5: What is Binary Classification? Provide examples.**

**Definition:** Binary Classification classifies data into one of two mutually exclusive classes.

**Diagram:**
```
Input Data → Classifier → {Class 0, Class 1}
```

**Examples:** Spam/Not Spam, Fraud/No Fraud, Benign/Malignant.

---

**QUESTION 6: Discuss performance evaluation metrics for binary classification.**

**Definition:** Metrics quantify how well the classifier distinguishes between positive and negative classes using a Confusion Matrix.

**Confusion Matrix (Compulsory):**
| Actual \ Predicted | Positive | Negative |
|-------------------|----------|----------|
| Positive | TP | FN |
| Negative | FP | TN |

**Formulas (Compulsory):**
1. **Accuracy:** $\frac{TP+TN}{TP+TN+FP+FN}$
2. **Precision:** $\frac{TP}{TP+FP}$
3. **Recall:** $\frac{TP}{TP+FN}$
4. **F1-Score:** $2 \times \frac{Precision \times Recall}{Precision + Recall}$

---

**QUESTION 7: Explain various ways to visualize binary classification performance.**

**Definition:** Visualization helps intuitively understand model behavior, errors, and trade-offs.

**Types:**
1. **Confusion Matrix Heatmap:** Shows TP, TN, FP, FN counts.
2. **ROC Curve:** Plots TPR vs FPR.
3. **Precision-Recall Curve:** Useful for imbalanced data.

---

**QUESTION 8: What is multi-class classification? How does it differ from binary?**

**Definition:** Multi-class classification assigns inputs to one of three or more classes.

**Strategies:**
- **One-vs-Rest (OvR):** One classifier per class.
- **One-vs-One (OvO):** One classifier per pair.

**Comparison:**
- **Binary:** 2 Classes.
- **Multi-class:** >2 Classes.

---

**QUESTION 9: What is unsupervised learning? Explain clustering and dimensionality reduction.**

**Definition:** Unsupervised learning finds hidden structures in unlabeled data without predefined outputs.

**Clustering:** Grouping similar data points (e.g., K-Means).
**Dimensionality Reduction:** Reducing feature count while preserving info (e.g., PCA).

**Diagram:**
```
Unlabeled Data → Algorithm → Patterns/Clusters
```

---

**UNIT – III**

**QUESTION 1: Explain Decision Tree representation with a neat diagram.**

**Definition:** A Decision Tree is a flowchart-like structure where internal nodes represent tests on attributes, branches represent outcomes, and leaf nodes represent class labels.

**Components:** Root Node, Decision Node, Leaf Node.

**Diagram (Compulsory):**
```
                 [Outlook]
               /     |      \
           Sunny   Overcast   Rain
            |         |         |
        [Humidity]  Play     [Wind]
         /    \                 /   \
      High   Normal          Weak   Strong
       |        |              |        |
     No       Yes            Yes       No
```

---

**QUESTION 2: Describe the basic decision tree learning algorithm.**

**Definition:** The algorithm recursively splits the dataset based on the attribute that provides the best information gain (or Gini index) until all data is pure.

**Steps:**
1. Select best attribute for root.
2. Split data into subsets.
3. Repeat process for every subset.
4. Stop when all instances have same class or no attributes left.

---

**QUESTION 3: Explain the ID3 algorithm with a suitable example.**

**Definition:** ID3 uses Entropy and Information Gain to build a decision tree top-down.

**Entropy Formula (Compulsory):**
$$Entropy(S) = - \sum p_i \log_2 p_i$$

**Information Gain Formula (Compulsory):**
$$IG(S, A) = Entropy(S) - \sum \frac{|S_v|}{|S|} Entropy(S_v)$$

**Rules:** Select attribute with highest IG.

---

**QUESTION 4: Compare Decision Tree learning with Linear Models.**

**Definition:** Decision Trees use non-linear rule-based splitting, while Linear Models assume a linear relationship between variables.

**Comparison Table:**
| Aspect | Decision Tree | Linear Model |
|--------|--------------|--------------|
| Relationship | Non-linear | Linear |
| Interpretability | High | Moderate |
| Boundary | Complex | Straight Line |

---

**QUESTION 5: Explain Linear Regression using the Least Squares Method.**

**Definition:** Least Squares minimizes the sum of squared differences between observed and predicted values to find the best fit line.

**Formulas (Compulsory):**
Slope: $m = \frac{n(\sum xy) - (\sum x)(\sum y)}{n(\sum x^2) - (\sum x)^2}$
Intercept: $c = \frac{\sum y - m(\sum x)}{n}$

**Goal:** Minimize $\sum(y - \hat{y})^2$.

---

**QUESTION 6: Describe Support Vector Machines (SVM).**

**Definition:** SVM finds a hyperplane that maximizes the margin between different classes in the feature space.

**Key Concepts:** Hyperplane, Margin, Support Vectors.

**Diagram:**
```
Class +1        |        Class -1
  ●   ●         |         ○   ○
      ●         |     ○
----------------|----------------  ← Hyperplane
      ●         |         ○
```

---

**QUESTION 7: Explain kernel methods and non-linear classification.**

**Definition:** Kernel methods map data into higher dimensions to make it linearly separable without explicit calculation (Kernel Trick).

**Common Kernels (Formulas):**
1. **Linear:** $K(x,y) = x \cdot y$
2. **Polynomial:** $K(x,y) = (x \cdot y + c)^d$
3. **RBF:** $K(x,y) = e^{-\gamma ||x-y||^2}$

---

**QUESTION 8: Explain the Perceptron model and its learning algorithm.**

**Definition:** The Perceptron is a single-layer neural network used for binary classification using a linear activation function.

**Model:**
$$y = f(\sum w_i x_i + b)$$

**Learning Rule:**
$$w_{new} = w_{old} + \eta (target - output) \cdot x$$

**Diagram:**
```
x1 ──(w1)──┐
x2 ──(w2)──┼──► Σ ──► Step ──► Output
x3 ──(w3)──┘
```

---

**QUESTION 9: Discuss advantages and limitations of Decision Trees and SVMs.**

**Decision Trees:**
- **Pros:** Interpretable, handles non-linear data.
- **Cons:** Prone to overfitting.

**SVMs:**
- **Pros:** Accurate in high dimensions, robust.
- **Cons:** Slow on large datasets, hard to interpret.

---

**UNIT – IV**

**QUESTION 1: Explain distance-based learning.**

**Definition:** Algorithms that make predictions based on the similarity (distance) between data points.

**Distance Metrics:**
1. **Euclidean:** $\sqrt{\sum (x_i - y_i)^2}$
2. **Manhattan:** $\sum |x_i - y_i|$
3. **Minkowski:** $(\sum |x_i - y_i|^p)^{1/p}$

---

**QUESTION 2: Explain K-Nearest Neighbour (KNN).**

**Definition:** KNN classifies a data point based on the majority class of its 'k' nearest neighbors.

**Diagram:**
```
 ●   ●              ○
      ●         x   ○   ← New Point
 ●                  ○
```
*(If k=3, majority is Class ●)*

---

**QUESTION 3: Explain K-Means clustering algorithm.**

**Definition:** K-Means partitions data into K clusters by minimizing the variance within each cluster.

**Steps:**
1. Initialize K centroids.
2. Assign points to nearest centroid.
3. Update centroids (mean of points).
4. Repeat until convergence.

---

**QUESTION 4: Explain K-Medoids.**

**Definition:** K-Medoids is similar to K-Means but uses actual data points (medoids) as centers instead of means (centroids).

**Key Difference:** Robust to outliers compared to K-Means.

---

**QUESTION 5: Compare K-Means and K-Medoids.**

**Comparison Table:**
| Aspect | K-Means | K-Medoids |
|--------|---------|-----------|
| Center | Mean (Virtual) | Medoid (Actual) |
| Outliers | Sensitive | Robust |
| Complexity | Low | High |

---

**QUESTION 6: Explain the Naïve Bayes classifier.**

**Definition:** A probabilistic classifier based on Bayes' Theorem with an assumption of independence between features.

**Bayes Theorem (Compulsory):**
$$P(C|X) = \frac{P(X|C)P(C)}{P(X)}$$

**Naïve Assumption:** $P(X|C) = P(x_1|C) \times P(x_2|C) \dots$

---

**QUESTION 7: Explain the Expectation–Maximization (EM) algorithm.**

**Definition:** An iterative algorithm to find maximum likelihood estimates of parameters in models with hidden variables.

**Steps:**
1. **E-Step:** Estimate hidden variables.
2. **M-Step:** Maximize parameters using estimates.

---

**QUESTION 8: Explain Gaussian Mixture Models (GMM).**

**Definition:** GMM assumes data is generated from a mixture of several Gaussian distributions.

**Formula:**
$$p(x) = \sum \pi_k \mathcal{N}(x | \mu_k, \Sigma_k)$$

**Use Case:** Soft clustering (probabilistic assignment).

---

**UNIT – V**

**QUESTION 1: Describe neural network representation with a neat diagram.**

**Definition:** A network of interconnected nodes (neurons) organized in layers (Input, Hidden, Output) that processes information in parallel.

**Diagram (Compulsory):**
```
Input Layer      Hidden Layer        Output Layer
 x1  ──●──┐
 x2  ──●──┼──► ● ──► ● ──► Output
 x3  ──●──┘        ●
```

---

**QUESTION 2: Discuss characteristics of problems suitable for neural network learning.**

**Definition:** NNs are suitable for problems with complex, non-linear patterns, large datasets, and high-dimensional inputs.

**Characteristics:**
1. Non-linear relationships.
2. Large amount of data.
3. Noisy or incomplete data.
4. High-dimensional input (e.g., Images).

---

**QUESTION 3: Explain single-layer and multi-layer neural networks.**

**Definition:** Single-layer has no hidden layers; Multi-layer has one or more hidden layers enabling non-linear mapping.

**Diagram Single-Layer:**
```
Input → Sum → Output
```
**Diagram Multi-Layer:**
```
Input → Hidden → Output
```

---

**QUESTION 4: Describe the Backpropagation algorithm.**

**Definition:** Backpropagation trains multi-layer networks by calculating the gradient of the loss function and updating weights from output to input.

**Weight Update Rule:**
$$w_{new} = w_{old} - \eta \frac{\partial Error}{\partial w}$$

**Steps:** Forward Pass -> Calculate Error -> Backward Pass -> Update Weights.

---

**QUESTION 5: Describe common issues in training neural networks.**

**Definition:** Training NNs faces challenges like overfitting, slow convergence, and unstable gradients.

**Issues:**
1. **Overfitting:** Model memorizes data. (Solution: Regularization).
2. **Vanishing Gradient:** Gradients become too small. (Solution: ReLU).
3. **Local Minima:** Gets stuck in sub-optimal solution.

---

**QUESTION 6: Describe different types of learning tasks in Reinforcement Learning.**

**Definition:** RL tasks vary based on whether the agent has a model of the environment and how it learns.

**Types:**
1. **Episodic:** Tasks with a terminal state (e.g., Chess).
2. **Continuous:** Ongoing tasks (e.g., Robot walking).
3. **Model-Based:** Uses a model of the environment.
4. **Model-Free:** Learns directly from experience (e.g., Q-Learning).

---

**QUESTION 7: Explain the Reinforcement Learning framework.**

**Definition:** RL involves an agent interacting with an environment to maximize cumulative reward through trial and error.

**Diagram (Compulsory):**
```
        Action (A)
     ┌──────────────┐
     │              ▼
   Agent        Environment
     ▲              │
     │              │
     └── Reward (R) │
        State (S) ──┘
```

**Components:** Agent, Environment, State, Action, Reward.

---

**QUESTION 8: Compare Reinforcement Learning with Supervised and Unsupervised Learning.**

**Comparison Table:**
| Aspect | Supervised | Unsupervised | Reinforcement |
|--------|------------|--------------|----------------|
| Data | Labeled | Unlabeled | None |
| Feedback | Direct | None | Rewards |
| Goal | Prediction | Patterns | Policy |
| Example | Classification | Clustering | Robotics |

---

**QUESTION 9: Explain the Q-Learning algorithm.**

**Definition:** A model-free RL algorithm that learns the value of actions (Q-values) to update a Q-table.

**Update Formula (Compulsory):**
$$Q(s,a) \leftarrow Q(s,a) + \alpha [r + \gamma \max Q(s',a') - Q(s,a)]$$

**Steps:** Initialize Q-table -> Choose Action (Epsilon-greedy) -> Update Q-value -> Repeat.
</div>
