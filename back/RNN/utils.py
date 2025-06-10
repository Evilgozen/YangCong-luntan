import numpy as np

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

def smooth(loss, cur_loss):
    return loss * 0.999 + cur_loss * 0.001

def print_sample(sample_ix, ix_to_char):
    txt = ''.join(ix_to_char[ix] for ix in sample_ix)
    if txt[0] == '的':
        txt = txt[1:]
    # txt = txt[0].upper() + txt[1:]  # capitalize first character 
    print ('%s' % (txt, ), end='')

def get_initial_loss(vocab_size, seq_length):
    return -np.log(1.0/vocab_size)*seq_length

def initialize_parameters(n_a, n_x, n_y):
    """
    Initialize parameters with small random values
    
    Returns:
    parameters -- python dictionary containing:
                        Wax -- Weight matrix multiplying the input, numpy array of shape (n_a, n_x)
                        Waa -- Weight matrix multiplying the hidden state, numpy array of shape (n_a, n_a)
                        Wya -- Weight matrix relating the hidden-state to the output, numpy array of shape (n_y, n_a)
                        b --  Bias, numpy array of shape (n_a, 1)
                        by -- Bias relating the hidden-state to the output, numpy array of shape (n_y, 1)
    """
    np.random.seed(1)
    Wax = np.random.randn(n_a, n_x)*0.01 # input to hidden
    Waa = np.random.randn(n_a, n_a)*0.01 # hidden to hidden
    Wya = np.random.randn(n_y, n_a)*0.01 # hidden to output
    b = np.zeros((n_a, 1)) # hidden bias
    by = np.zeros((n_y, 1)) # output bias
    
    parameters = {"Wax": Wax, "Waa": Waa, "Wya": Wya, "b": b, "by": by}
    
    return parameters

def rnn_step_forward(parameters, a_prev, x):
    
    Waa, Wax, Wya, by, b = parameters['Waa'], parameters['Wax'], parameters['Wya'], parameters['by'], parameters['b']
    a_next = np.tanh(np.dot(Wax, x) + np.dot(Waa, a_prev) + b)
    p_t = softmax(np.dot(Wya, a_next) + by)
    
    return a_next, p_t

def rnn_forward(X, Y, a0, parameters, vocab_size = 27):
    
    # Initialize x, a and y_hat as empty dictionaries
    x, a, y_hat = {}, {}, {}
    
    a[-1] = np.copy(a0)
    
    # initialize your loss to 0
    loss = 0
    
    for t in range(len(X)):
        
        # Set x[t] to be the one-hot vector representation of the t'th character in X.
        # if X[t] == None, we just have x[t]=0. This is used to set the input for the first timestep to the zero vector.
        x[t] = np.zeros((vocab_size,1))
        if (X[t] != None):
            x[t][X[t]] = 1
        
        # Run one step forward of the RNN
        a[t], y_hat[t] = rnn_step_forward(parameters, a[t-1], x[t])
        
        # Update the loss by substracting the cross-entropy term of this time-step from it.
        loss -= np.log(y_hat[t][Y[t],0])
        
    cache = (y_hat, a, x)
        
    return loss, cache

def rnn_step_backward(dy, gradients, parameters, x, a, a_prev):
    
    gradients['dWya'] += np.dot(dy, a.T)
    gradients['dby'] += dy
    da = np.dot(parameters['Wya'].T, dy) + gradients['da_next'] # backprop into h
    daraw = (1 - a * a) * da # backprop through tanh nonlinearity
    gradients['db'] += daraw
    gradients['dWax'] += np.dot(daraw, x.T)
    gradients['dWaa'] += np.dot(daraw, a_prev.T)
    gradients['da_next'] = np.dot(parameters['Waa'].T, daraw)
    
    return gradients

def rnn_backward(X, Y, parameters, cache):
    # Initialize gradients as an empty dictionary
    gradients = {}
    
    # Retrieve from cache and parameters
    (y_hat, a, x) = cache
    Waa, Wax, Wya, by, b = parameters['Waa'], parameters['Wax'], parameters['Wya'], parameters['by'], parameters['b']
    
    # each one should be initialized to zeros of the same dimension as its corresponding parameter
    gradients['dWax'], gradients['dWaa'], gradients['dWya'] = np.zeros_like(Wax), np.zeros_like(Waa), np.zeros_like(Wya)
    gradients['db'], gradients['dby'] = np.zeros_like(b), np.zeros_like(by)
    gradients['da_next'] = np.zeros_like(a[0])
    
    # Backpropagate through time
    for t in reversed(range(len(X))):
        dy = np.copy(y_hat[t])
        dy[Y[t]] -= 1
        gradients = rnn_step_backward(dy, gradients, parameters, x[t], a[t], a[t-1])
    
    return gradients, a

def update_parameters(parameters, gradients, learning_rate):
    
    parameters['Wax'] += -learning_rate * gradients['dWax']
    parameters['Waa'] += -learning_rate * gradients['dWaa']
    parameters['Wya'] += -learning_rate * gradients['dWya']
    parameters['b']  += -learning_rate * gradients['db']
    parameters['by']  += -learning_rate * gradients['dby']
    
    return parameters

def clip(gradients, maxValue):
    """
    Clips the gradients' values between minimum and maximum.
    
    Arguments:
    gradients -- a dictionary containing the gradients "dWaa", "dWax", "dWya", "db", "dby"
    maxValue -- everything above this number is set to this number, and everything below -maxValue is set to -maxValue
    
    Returns: 
    gradients -- a dictionary with the clipped gradients.
    """
    dWaa, dWax, dWya, db, dby = gradients['dWaa'], gradients['dWax'], gradients['dWya'], gradients['db'], gradients['dby']
   
    # clip to mitigate exploding gradients
    for gradient in [dWaa, dWax, dWya, db, dby]:
        np.clip(gradient, -maxValue, maxValue, out=gradient)
    
    gradients = {"dWaa": dWaa, "dWax": dWax, "dWya": dWya, "db": db, "dby": dby}
    
    return gradients

def sample(parameters, char_to_ix, seed, max_length=50, min_length=2, exact_length=False):
    """
    Sample a sequence of characters according to a sequence of probability distributions output of the RNN
    
    Arguments:
    parameters -- python dictionary containing the parameters Waa, Wax, Wya, by, and b. 
    char_to_ix -- python dictionary mapping each character to an index.
    seed -- integer, random seed
    max_length -- integer, maximum length of the generated sequence
    min_length -- integer, minimum length of the generated sequence
    exact_length -- boolean, if True, tries to generate a sequence of exactly max_length characters
    
    Returns:
    indices -- a list of length n containing the indices of the sampled characters.
    """
    
    # Retrieve parameters and relevant shapes from parameters dictionary
    Waa, Wax, Wya, by, b = parameters['Waa'], parameters['Wax'], parameters['Wya'], parameters['by'], parameters['b']
    vocab_size = by.shape[0]
    n_a = Waa.shape[1]
    
    # Create the one-hot vector x for the first character (dummy character)
    x = np.zeros((vocab_size, 1))
    # Initialize a_prev as zeros
    a_prev = np.zeros((n_a, 1))
    
    # Create an empty list of indices
    indices = []
    
    # idx is the index of the one-hot vector x that is set to 1
    # All other positions in x are zero.
    idx = -1 
    
    # Loop over time-steps t. At each time-step, sample a character from a probability distribution
    # and append its index to "indices". We'll stop if we reach max_length characters
    # or if we encounter the end character (if it exists)
    counter = 0
    
    # 检查是否有结束字符，如果没有就不使用结束字符条件
    has_end_char = False
    end_char_idx = -1
    
    if '\n' in char_to_ix:
        has_end_char = True
        end_char_idx = char_to_ix['\n']
    
    np.random.seed(seed)
    
    # 如果需要精确长度，则不考虑结束字符，直接生成到指定长度
    if exact_length:
        while counter < max_length:
            # Forward propagate x
            a = np.tanh(np.dot(Wax, x) + np.dot(Waa, a_prev) + b)
            z = np.dot(Wya, a) + by
            y = softmax(z)
            
            # Sample the index of a character within the vocabulary from the probability distribution y
            idx = np.random.choice(list(range(vocab_size)), p=y.ravel())
            
            # 如果是结束字符且还没达到最小长度，重新采样
            if has_end_char and idx == end_char_idx and counter < min_length - 1:
                continue
                
            # Append the index to "indices"
            indices.append(idx)
            
            # Overwrite the input character as the one corresponding to the sampled index.
            x = np.zeros((vocab_size, 1))
            x[idx] = 1
            
            # Update "a_prev" to be "a"
            a_prev = a
            
            counter += 1
            
        # 如果需要精确长度，确保最后一个字符是结束字符
        if has_end_char and indices[-1] != end_char_idx:
            indices[-1] = end_char_idx
    else:
        # 原来的逻辑：生成直到遇到结束字符或达到最大长度
        while ((not has_end_char or idx != end_char_idx) and counter < max_length) or counter < min_length:
            # Forward propagate x
            a = np.tanh(np.dot(Wax, x) + np.dot(Waa, a_prev) + b)
            z = np.dot(Wya, a) + by
            y = softmax(z)
            
            # Sample the index of a character within the vocabulary from the probability distribution y
            idx = np.random.choice(list(range(vocab_size)), p=y.ravel())
            
            # 如果是结束字符且还没达到最小长度，重新采样
            if has_end_char and idx == end_char_idx and counter < min_length - 1:
                continue
                
            # Append the index to "indices"
            indices.append(idx)
            
            # Overwrite the input character as the one corresponding to the sampled index.
            x = np.zeros((vocab_size, 1))
            x[idx] = 1
            
            # Update "a_prev" to be "a"
            a_prev = a
            
            counter += 1
            
        # 如果达到最大计数并且有结束字符，添加结束字符
        if counter == max_length and has_end_char and indices[-1] != end_char_idx:
            indices.append(end_char_idx)
    
    return indices

def optimize(X, Y, a_prev, parameters, learning_rate = 0.01, vocab_size = 27):
    """
    Execute one step of the optimization to train the model.
    
    Arguments:
    X -- list of integers, where each integer is a number that maps to a character in the vocabulary.
    Y -- list of integers, exactly the same as X but shifted one index to the left.
    a_prev -- previous hidden state.
    parameters -- python dictionary containing:
                        Wax -- Weight matrix multiplying the input, numpy array of shape (n_a, n_x)
                        Waa -- Weight matrix multiplying the hidden state, numpy array of shape (n_a, n_a)
                        Wya -- Weight matrix relating the hidden-state to the output, numpy array of shape (n_y, n_a)
                        b --  Bias, numpy array of shape (n_a, 1)
                        by -- Bias relating the hidden-state to the output, numpy array of shape (n_y, 1)
    learning_rate -- learning rate for the model.
    
    Returns:
    loss -- value of the loss function (cross-entropy)
    gradients -- python dictionary containing:
                        dWax -- Gradients of input-to-hidden weights, of shape (n_a, n_x)
                        dWaa -- Gradients of hidden-to-hidden weights, of shape (n_a, n_a)
                        dWya -- Gradients of hidden-to-output weights, of shape (n_y, n_a)
                        db -- Gradients of bias vector, of shape (n_a, 1)
                        dby -- Gradients of output bias vector, of shape (n_y, 1)
    a[len(X)-1] -- the last hidden state, of shape (n_a, 1)
    """
    
    # Forward propagate through time
    loss, cache = rnn_forward(X, Y, a_prev, parameters, vocab_size)
    
    # Backpropagate through time
    gradients, a = rnn_backward(X, Y, parameters, cache)
    
    # Clip your gradients between -5 (min) and 5 (max)
    gradients = clip(gradients, 5)
    
    # Update parameters
    parameters = update_parameters(parameters, gradients, learning_rate)
    
    return loss, gradients, a[len(X)-1]
