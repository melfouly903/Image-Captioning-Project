# 🖼️ Image Captioning Project (CNN + RNN)

This project implements an **Image Captioning system** that automatically generates textual descriptions for input images using a hybrid Deep Learning model combining **Convolutional Neural Networks (CNN)** and **Recurrent Neural Networks (RNN)**.

## 🚀 Overview

The model takes an image as input, extracts its visual features using a pretrained CNN, and then generates a meaningful caption word-by-word using an RNN (LSTM).

## 🧠 Model Architecture

* **CNN (Feature Extractor):**

  * Pretrained model (e.g., MobileNet / VGG16) to extract image features.
* **RNN (Sequence Generator):**

  * LSTM network to generate captions based on extracted features.

## 📊 Dataset

* Images and captions were collected using **web scraping techniques** (e.g., Reddit / image platforms).
* The dataset was preprocessed by:

  * Resizing images
  * Cleaning and tokenizing text
  * Converting words into numerical sequences

## ⚙️ Technologies Used

* Python
* TensorFlow / Keras
* NumPy, Pandas
* BeautifulSoup / Requests (for web scraping)
* NLTK (for text preprocessing)

## 🔍 Features

* Generate captions for unseen images
* Simple and efficient architecture
* Lightweight dataset for fast training

## 📈 Future Improvements

* Add Attention Mechanism for better caption quality
* Increase dataset size for improved accuracy
* Build a GUI for user interaction

## 📌 How to Run

1. Clone the repository
2. Install dependencies
3. Run the training script
4. Test the model on new images

## 👨‍💻 Author

Mohamed Elfoly
