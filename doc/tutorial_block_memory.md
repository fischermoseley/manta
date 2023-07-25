## Welcome Back!

We're going to jump right on in on this one. Today's testing is going to focus on one of the cornerstones of our medium-scale FPGA projects - the BRAM! Manta's been designed primarily as a debugging tool - but more generally its purpose is to shuffle data about. And a BRAM is one of the more useful places on a FPGA that it can go.

In today's exercise, we'll be revisitng our lab03 (popcat pong) code, which used a BRAM to store the contents of an image, which we rendered as a sprite. Here we'll be doing almost exactly the same thing, except we'll be hooking our BRAM up to Manta, which will let us put whatever image we'd like into the BRAM. We'll just be sending data _into_ the BRAM, but we could just as easily pull data out of it - say if we had a VGA camera connected to our board that dumped images into a framebuffer, which we wanted to dump to a host machine.

This should hopefully be nice and quick. Go ahead and grab the starter code from here:


And just like last time, we'll need to create a config file that defines our BRAM - what it's called, how many bits wide the input is, and how many entries it has (depth). Here's an example configureation:


```yaml
mam: bro
```

Go ahead and make a configuration of your own like this, and name it something super creative and interesting. I named mine `manta.yaml`.