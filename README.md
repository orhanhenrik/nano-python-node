# nano-python
This is an implementation of the [Nano](https://nano.org) protocol in Python 3. It will be fully compatible and be able to talk to any other complete node implementation on the network.  
  
I have chosen to use Python because of it's ease of use, good ecosystem and relatively good performance. All CPU-intensive tasks will be done in C/C++ combined with python bindings in the future.  
With asyncio (event loop) we get fast performance and parallel execution without having to worry about thread safety.  

## Progress
This project is a work in progress.  
I have currently managed to parse all incoming UDP messages and am working on the TCP protocol.  
I can validate the PoW and signature of a block or vote.  
I reply to keepalives with an empty keepalive, but no other messages are sent to peers at the moment.
