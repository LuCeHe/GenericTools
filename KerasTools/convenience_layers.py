import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.keras.layers import Input, Embedding, \
    LSTM, Lambda, Dense, Layer
from tensorflow.keras.models import Model

from GenericTools.TFTools.convenience_operations import slice_from_to, clip_layer, replace_column


class AverageOverAxis(Layer):
    def __init__(self, axis, name='AverageOverAxis', **kwargs):
        self.axis = axis
        super(AverageOverAxis, self).__init__(**kwargs, name=name)

    def call(self, inputs):
        return K.mean(inputs, axis=self.axis)

    def compute_output_shape(self, input_shape):
        input_shape = list(input_shape)
        input_shape.pop(self.axis)
        return tuple(input_shape)


class ExpandDims(object):

    def __init__(self, axis):
        self.axis = axis

    def __call__(self, inputs):
        def ed(tensor, axis):
            expanded = K.expand_dims(tensor, axis=axis)
            return expanded

        return Lambda(ed, arguments={'axis': self.axis})(inputs)


class Squeeze(object):

    def __init__(self, axis):
        self.axis = axis

    def __call__(self, inputs):
        def squeeze(tensor, axis):
            squeezed = K.squeeze(tensor, axis=axis)
            return squeezed

        return Lambda(squeeze, arguments={'axis': self.axis})(inputs)


class Slice(Layer):

    # FIXME: axis parameter is not functional
    def __init__(self, axis, initial, final, **kwargs):
        self.axis, self.initial, self.final = axis, initial, final
        super(Slice, self).__init__(**kwargs)

    def build(self, input_shape):
        super(Slice, self).build(input_shape)

    def call(self, inputs):
        output = slice_from_to(inputs, self.initial, self.final)
        return output


class RepeatElements(Layer):
    def __init__(self, n_head, **kwargs):
        self.n_head = n_head
        super(RepeatElements, self).__init__(**kwargs)

    def build(self, input_shape):
        super(RepeatElements, self).build(input_shape)

    def call(self, inputs):
        repeated = K.repeat_elements(inputs, self.n_head, 0)
        return repeated

    def compute_output_shape(self, input_shape):
        input_shape[0] = input_shape[0] * self.n_head
        return input_shape


class Clip(object):

    def __init__(self, min_value=0., max_value=1.):
        self.min_value, self.max_value = min_value, max_value

    def __call_(self, inputs):
        return Lambda(clip_layer, arguments={'min_value': self.min_value, 'max_value': self.max_value})(inputs)


class ReplaceColumn(Layer):

    def __init__(self, column_position, **kwargs):
        super(ReplaceColumn, self).__init__(**kwargs)

        self.column_position = column_position

    def call(self, inputs, training=None):
        matrix, column = inputs

        matrix = tf.cast(matrix, dtype=tf.float32)
        column = tf.cast(column, dtype=tf.float32)
        new_matrix = replace_column(matrix, column, self.column_position)
        new_matrix = tf.cast(new_matrix, dtype=tf.int32)
        return new_matrix


def predefined_model(vocab_size, emb_dim, units=128):
    embedding = Embedding(vocab_size, emb_dim, mask_zero='True')
    lstm = LSTM(units, return_sequences=False)

    input_question = Input(shape=(None,), name='discrete_sequence')
    embed = embedding(input_question)
    lstm_output = lstm(embed)
    softmax = Dense(vocab_size, activation='softmax')(lstm_output)

    return Model(inputs=input_question, outputs=softmax)


class OneHot(Layer):
    def __init__(self, n_out, **kwargs):
        self.n_out = n_out
        kwargs['name'] = 'onehot'
        super(OneHot, self).__init__(**kwargs)

    def build(self, input_shape):
        super(OneHot, self).build(input_shape)

    def call(self, inputs):
        inputs = tf.cast(inputs, tf.int32)
        return tf.one_hot(inputs, depth=self.n_out)

    def compute_output_shape(self, input_shape):
        output_shape = input_shape
        output_shape[-1] = self.n_out

        input_shape[0] = input_shape[0] * self.n_head
        return input_shape

    def get_config(self):
        return {'n_out': self.n_out}
