import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (Input, Embedding, LSTM, Bidirectional,
                                     Dense, Dropout, BatchNormalization,
                                     SpatialDropout1D, GlobalMaxPooling1D)
from tensorflow.keras.optimizers import Adam

def build_bilstm_classifier(vocab_size, max_len, embed_dim=128, lstm_units=128, n_classes=3):
    """
    Builds a Bi-LSTM Classifier for price categorization.
    """
    inp = Input(shape=(max_len,), name='text_input')
    x   = Embedding(vocab_size, embed_dim, mask_zero=True, name='embedding')(inp)
    x   = SpatialDropout1D(0.3)(x)
    x   = Bidirectional(LSTM(lstm_units, return_sequences=True,
                              dropout=0.3, recurrent_dropout=0.2))(x)
    x   = Bidirectional(LSTM(lstm_units // 2,
                              dropout=0.3, recurrent_dropout=0.2))(x)
    x   = BatchNormalization()(x)
    x   = Dense(64, activation='relu')(x)
    x   = Dropout(0.4)(x)
    out = Dense(n_classes, activation='softmax', name='class_output')(x)
    model = Model(inp, out)
    model.compile(optimizer=Adam(1e-3),
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    return model

def build_bilstm_regressor(vocab_size, max_len, embed_dim=128, lstm_units=128):
    """
    Builds a Bi-LSTM Regressor for continuous price prediction.
    """
    inp = Input(shape=(max_len,), name='text_input')
    x   = Embedding(vocab_size, embed_dim, mask_zero=True)(inp)
    x   = SpatialDropout1D(0.3)(x)
    x   = Bidirectional(LSTM(lstm_units, return_sequences=True,
                              dropout=0.3, recurrent_dropout=0.2))(x)
    x   = GlobalMaxPooling1D()(x)
    x   = BatchNormalization()(x)
    x   = Dense(64, activation='relu')(x)
    x   = Dropout(0.4)(x)
    out = Dense(1, activation='sigmoid', name='price_output')(x)
    model = Model(inp, out)
    model.compile(optimizer=Adam(1e-3), loss='mse', metrics=['mae'])
    return model
