# -*- coding: utf-8 -*-
"""Grammer Correction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CgAWF8yBdtpqyhHM_i1tMee6wrvbuYPb
"""

!pip install torch==1.8.1+cu111 torchvision==0.9.1+cu111 torchaudio===0.8.1 -f https://download.pytorch.org/whl/lts/1.8/torch_lts.html

from google.colab import drive
drive.mount('/content/gdrive')

!ln -s /content/gdrive/My\ Drive/ /mydrive
!ls /mydrive

!pip3 install pip==20.1.1

!pip3 install git+https://github.com/PrithivirajDamodaran/Gramformer.git

from gramformer import Gramformer

from gramformer import Gramformer
import torch

def set_seed(seed):
  torch.manual_seed(seed)
  if torch.cuda.is_available():
    torch.cuda.manual_seed_all(seed)

set_seed(1212)


gf = Gramformer(models = 1, use_gpu=False) # 1=corrector, 2=detector

influent_sentences = [
    "He are moving here.",
    "I am doing fine. How is you?",
    "How is they?",
    "Matt like fish",
    "the collection of letters was original used by the ancient Romans",
    "We enjoys horror movies",
    "Anna and Mike is going skiing",
    "I walk to the store and I bought milk",
    " We all eat the fish and then made dessert",
    "I will eat fish for dinner and drink milk",
    "what be the reason for everyone leave the company",
]   

for influent_sentence in influent_sentences:
    corrected_sentences = gf.correct(influent_sentence, max_candidates=1)
    print("[Input] ", influent_sentence)
    for corrected_sentence in corrected_sentences:
      print("[Correction] ",corrected_sentence)
    print("-" *100)

import re


def clean_text(txt):
    txt = txt.lower()
    txt = re.sub(r"i'm", "i am", txt)
    txt = re.sub(r"it's", "it is", txt)
    txt = re.sub(r"he's", "he is", txt)
    txt = re.sub(r"she's", "she is", txt)
    txt = re.sub(r"that's", "that is", txt)
    txt = re.sub(r"what's", "what is", txt)
    txt = re.sub(r"where's", "where is", txt)
    txt = re.sub(r"\'ll", " will", txt)
    txt = re.sub(r"\'ve", " have", txt)
    txt = re.sub(r"\'re", " are", txt)
    txt = re.sub(r"\'d", " would", txt)
    txt = re.sub(r"won't", "will not", txt)
    txt = re.sub(r"can't", "can not", txt)

    return txt


def create_training_data():
    data_path = r'/mydrive/Maruf/Final_Everything/Arcadia/human_text.txt'
    data_path2 = r'/mydrive/Maruf/Final_Everything/Arcadia/robot_text.txt'
    # Defining lines as a list of each line
    with open(data_path, "r", encoding='utf-8') as f:
        lines = f.read().split('\n')
    with open(data_path2, "r", encoding='utf-8') as f:
        lines2 = f.read().split('\n')
    lines = [re.sub(r"\[\w+\]", 'hi', line) for line in lines]
    lines = [" ".join(re.findall(r"\w+", line)) for line in lines]
    lines2 = [re.sub(r"\[\w+\]", '', line) for line in lines2]
    lines2 = [" ".join(re.findall(r"\w+", line)) for line in lines2]

    encoder_input_data = []
    decoder_input_data = []
    decoder_output_data = []


    for i in range(len(lines)):
        encoder_input_data.append(clean_text(lines[i]))
        decoder_input_data.append('<sos> ' + clean_text(lines2[i]))
        decoder_output_data.append(clean_text(lines2[i]) + ' <eos>')
    return encoder_input_data, decoder_input_data, decoder_output_data


create_training_data()


VOCAB_SIZE = 5000
MAXLEN = 40
EPOCHS = 150
BATCH_SIZE = 1024
VERBOSE = 1
SAVE_AT = 50
LEARNING_RATE = 0.01
LOSS = 'sparse_categorical_crossentropy'
a,b,c=create_training_data()
c[:5]

import numpy as np
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Bidirectional, Embedding
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras import Input
from tensorflow.keras.models import load_model
from tensorflow.keras.regularizers import l2
from tensorflow.keras.layers import Lambda


def seq2seq():
    encoder_inputs= Input(shape=(40,))
    encoder_embedding = Embedding(VOCAB_SIZE, 100, input_length=MAXLEN)

    decoder_embedding = Embedding(VOCAB_SIZE, 100, input_length=MAXLEN)
    encoder_embeddings = encoder_embedding(encoder_inputs)
    encoder_lstm=LSTM(256, return_state=True, kernel_regularizer=l2(0.0000001), activity_regularizer=l2(0.0000001))
    LSTM_outputs, state_h, state_c = encoder_lstm(encoder_embeddings)

    encoder_states = [state_h, state_c]

    decoder_inputs = Input(shape=(40,), name='decoder_inputs')
    decoder_lstm = LSTM(256, return_sequences=True, return_state=True, name='decoder_lstm', kernel_regularizer=l2(0.0000001), activity_regularizer=l2(0.0000001))
    decoder_embeddings = decoder_embedding(decoder_inputs)
    decoder_outputs, _, _ = decoder_lstm(decoder_embeddings,
                                         initial_state=encoder_states)


    decoder_dense = Dense(5000, activation='softmax', name='decoder_dense')



    decoder_outputs = decoder_dense(decoder_outputs)
    print(decoder_outputs)
    seq2seq = Model([encoder_inputs, decoder_inputs], decoder_outputs, name='model_encoder_training')

    return seq2seq

import pickle
import re
import tensorflow as tf



class Tokenizer:
    def __init__(self, vocab_size=10000, maxlen=40, padding='post'):

        self.tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=VOCAB_SIZE, oov_token="<unk>",
                                                               filters='!"#$%&()*+.,-/:;=?@[\]^_`{|}~ ', split=' ')
        self.maxlen = maxlen
        self.padding = padding

    def tokenize_and_pad_training_data(self, encoder_input_data, decoder_input_data, decoder_output_data):
        text_corpus = encoder_input_data + decoder_input_data + decoder_output_data
        self.tokenizer.fit_on_texts(text_corpus)

        self.tokenizer.word_index['<pad>'] = 0
        self.tokenizer.index_word[0] = '<pad>'

        encoder_input_data_tokenized = self.tokenizer.texts_to_sequences(encoder_input_data)
        decoder_input_data_tokenized = self.tokenizer.texts_to_sequences(decoder_input_data)
        decoder_output_data_tokenized = self.tokenizer.texts_to_sequences(decoder_output_data)

        encoder_input_data_padded = tf.keras.preprocessing.sequence.pad_sequences(encoder_input_data_tokenized,
                                                                                  padding=self.padding,
                                                                                  maxlen=self.maxlen)
        decoder_input_data_padded = tf.keras.preprocessing.sequence.pad_sequences(decoder_input_data_tokenized,
                                                                                  padding=self.padding,
                                                                                  maxlen=self.maxlen)
        decoder_output_data_padded = tf.keras.preprocessing.sequence.pad_sequences(decoder_output_data_tokenized,
                                                                                   padding=self.padding,
                                                                                   maxlen=self.maxlen)

        return encoder_input_data_padded, decoder_input_data_padded, decoder_output_data_padded

    def decode_sequence(self, encoded_text):
        lst = []
        for i in encoded_text:
            lst.append(self.tokenizer.index_word[i])
        return ' '.join(lst)

    def tokenize_sequence(self, sequence):
        tokenized_sequence = []
        sequence = sequence.lower()
        sequence = sequence.strip()
        sequence = re.sub(r'[^\w\s]', '', sequence)
        for i in sequence.split(' '):
            try:
                tokenized_sequence.append(self.tokenizer.word_index[i])
            except:
                tokenized_sequence.append(self.tokenizer.word_index['well'])
        if len(tokenized_sequence) > 40:
            tokenized_sequence = tokenized_sequence[:40]
        elif len(tokenized_sequence) == 40:
            tokenized_sequence = tokenized_sequence
        else:
            length = len(tokenized_sequence)
        for i in range(40 - length):
            tokenized_sequence.append(0)
        return tokenized_sequence

    def save_tokenizer(self, name):
        with open(f'{name}.pickle', 'wb') as handle:
            pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load_tokenizer(self, path):
        with open(path, 'rb') as handle:
            tokenizer = pickle.load(handle)
            self.tokenizer = tokenizer
        return tokenizer

from math import log
import numpy as np
from tensorflow.keras import Input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense
from tensorflow.keras.regularizers import l2
from tensorflow.keras.layers import LSTM, Embedding

# +++++++++++++++++++++++++++++++++ seq2seq model to refere layers with their names ++++++++++++++++++++++++++++++++
encoder_inputs = Input(shape=(40,))
encoder_embedding = Embedding(VOCAB_SIZE, 100, input_length=MAXLEN)

decoder_embedding = Embedding(VOCAB_SIZE, 100, input_length=MAXLEN)
encoder_embeddings = encoder_embedding(encoder_inputs)
encoder_lstm = LSTM(256, return_state=True, kernel_regularizer=l2(0.0000001), activity_regularizer=l2(0.0000001))
LSTM_outputs, state_h, state_c = encoder_lstm(encoder_embeddings)

encoder_states = [state_h, state_c]

decoder_inputs = Input(shape=(40,), name='decoder_inputs')
decoder_lstm = LSTM(256, return_sequences=True, return_state=True, name='decoder_lstm',
                    kernel_regularizer=l2(0.0000001), activity_regularizer=l2(0.0000001))
decoder_embeddings = decoder_embedding(decoder_inputs)
decoder_outputs, _, _ = decoder_lstm(decoder_embeddings, initial_state=encoder_states)

decoder_dense = Dense(5000, activation='softmax', name='decoder_dense')
decoder_outputs = decoder_dense(decoder_outputs)

Seq2SeqModel = Model([encoder_inputs, decoder_inputs], decoder_outputs, name='model_encoder_training')

# +++++++++++++++++++++++++++++++++ model for predictions +++++++++++++++++++++++++++++++++
encoder_model = Model(encoder_inputs, encoder_states)

decoder_state_input_h = Input(shape=(256,))
decoder_state_input_c = Input(shape=(256,))
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]

decoder_inputs = Input(shape=(1,))
embedded = decoder_embedding(decoder_inputs)
decoder_outputs, state_h, state_c = decoder_lstm(embedded, initial_state=decoder_states_inputs)
decoder_states = [state_h, state_c]
decoder_outputs = decoder_dense(decoder_outputs)
decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs] + decoder_states)


# +++++++++++++++++++++++++++++++++ Predict Class +++++++++++++++++++++++++++++++++
class Predict():
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def create_response(self, question):
        question = np.expand_dims(self.tokenizer.tokenize_sequence(clean_text(question)), axis=0)
        result = self.predict_sentence(question)
        return result

    def predict_sentence(self, input_seq):
        with tf.device('/cpu:0'):
            states_value = encoder_model.predict(input_seq)

            target_seq = np.zeros((1, 1))
            target_seq[0, 0] = self.tokenizer.tokenizer.word_index['<sos>']
            output_sentence = []

            for _ in range(MAXLEN):
                output_tokens, h, c = decoder_model.predict([target_seq] + states_value)
                idx = np.argmax(output_tokens)

                if self.tokenizer.tokenizer.index_word[idx] == '<eos>':
                    break

                output_sentence.append(idx)
                target_seq[0, 0] = idx
                states_value = [h, c]

        return self.tokenizer.decode_sequence(output_sentence)

tokenizer = Tokenizer()

# loading tokenizer
tokenizer.load_tokenizer('/mydrive/Maruf/Final_Everything/Arcadia/tokenizer-vocab_size-5000.pickle')

# loading pretrained weight
Seq2SeqModel.load_weights('/mydrive/Maruf/Final_Everything/Arcadia/seq2seq-weights-800-epochs-0.01-learning_rate.h5')

predict = Predict(Seq2SeqModel, tokenizer)

def chatwithbot(text):
    return (predict.create_response(text))


print("Hello")

while True:
  text=input()
  corrected_text=gf.correct(text)
  #print(type(corrected_text[0][0]))
  if ( text == corrected_text[0][0]):
     reply=chatwithbot(corrected_text[0][0])
     print(reply) 
  
  else:
      print("Did you mean: ")
      print(corrected_text[0][0])
      yn=input()
      if(yn=="yes" or yn=="Yes"):
          reply=chatwithbot(corrected_text[0][0])
          print(reply)

print(type(text))

sentences = [
    'I like for walks', 
    'World is flat', 
    'Red a color', 
    'I wish my Computer was run faster.'
]

for sentence in sentences:
    res = gf.correct(sentence)
    print(res[0])

!pip install gradio

import gradio as gr

def correct(sentence):
    res = gf.correct(sentence) # Gramformer correct
    return res[0] # Return first value in res array

app_inputs = gr.inputs.Textbox(lines=2, placeholder="Enter sentence here...")

interface = gr.Interface(fn=correct, 
                        inputs=app_inputs,
                         outputs='text', 
                        title='Grammar Correction Interface Primary')

interface.launch()