# UNETTEST

![What is the answer, O Deep Thought](https://docs-unettest.s3.us-east-2.amazonaws.com/o_deep_thought.png)

When I write software, there are many ways to ask a question. I could go to
Stack Overflow or a smarter coworker, but I usually like to ask my computer
first. 

What do I do if my computer is making me wait [seven and a half million
years](https://hitchhikers.fandom.com/wiki/Deep_Thought) to get an answer? 

I would need to revisit the question of how to ask questions. If I want to know
the Ultimate Answer to Life, the Universe, and Everything, I must ask a damn
Ultimate Question. Otherwise I will end up with an answer like 42. 

42 is an interesting datapoint though, and it might be useful, but in order to
figure out what's going on, I might also like to know the answer to Death, the
Universe, and Everything. And I might like to ask a question about just the
Universe on its own, and maybe a question or two on that Everything bit. And
perhaps a couple of questions about a bowl of petunias. I cannot afford to wait
so long between each answer. I have things to do.

I do not have time to build Earth in order to ask my questions so instead I use
TDD. TDD is awesome. I can ask many questions quickly, and once I have asked a
question, I am confident it will remain answered. If I have a question on how
something should work, I write a test describing the behavior.  Then I run my
test and write code to make the test work. Great stuff. If there is a corner
case, I write a test case. And when my code turns red, I make it better.

I was writing NGINX configurations some time ago. I was new to NGINX and trying
to figure out how things work. Their documentation (lovely though it is) can be
impenetrable. I was getting the picture by looking at existing configurations
and mimicking what they do.  And given that this bouquet of CONF files was
handling all of our network traffic, it was largely a look-don't-touch affair.
If I had a question, I could not ask it of my computer easily. NGINX does not
have support for unit tests, or rapid feedback of any kind. If I really really
wanted to know the answer to a question, I'd have to deploy that question to
NonProd and wave around my dowsing rod to try and sense if things are both
working and not broken. High cost, low reliablity.

This is silly in the best of times, but workable--no reason to fix what
ain't broke. Until I started scratching around the corners of an edge case...
The only way I was able to figure out what on Earth was going on, I wanted to
walk through all the different potential logic paths, and ugh, that was not
pretty. Let's get into it.

## The Monolith and the Microservice

We have a Monolith that does all sorts of things. We are excising one piece of
it to turn into a Microservice with the goal of eventually putting the whole
Monolith down.

We have a playout system (actually, two systems) used by our radio teams that
sends us an update every few minutes. These requests come in through our NGINX
server and are typically routed to the Monolith. For now and into the
forseeable future, we want to support both the Monolith and the Microservice.
As a DevOps engineer on staff, I was asked to go write a rule in our NGINX
configuration to mirror the requests--they should go to both the Microservice
and the Monolith. This way, the Monolith would continue to work while the
Microservice was under development.

Seems easy enough. Referencing the NGINX docs, we could take the existing rule
and add a `mirror` directive to a special mirror location

```
location ~* /api/v1/impotant_update/([^\/]*) {
         proxy_pass $monolith$request_uri;

         mirror /microservice_mirror/$1$is_args$args; # NEW LINE!

         ...some other configurations
}
```

and then define the mirror route like this

```
location ~* /microservice_mirror/(.*) {
         internal;
         proxy_pass $microservice/new/api/update?value=$1$is_args$args;

         ...some other configurations
}
```

This way I could fulfill the requirements:

+ send incoming request to two servers, (a) and (b)
+ slightly reconfigure the incoming request to fit the api difference

Ok, with that done, I committed my NGINX changes and deployed to NonProd.
But... it did not work. The requests were not being mirrored correctly. I was
an NGINX beginner and the NGINX documentation, through complete and easy to
reference, is anything but beginner friendly. I thought my conf files were not
working due to my own ignorance. I thought I could learn how to fix the conf
files with that classic development strategy--guess and check.

But as I guessed and checked, NGINX's behavior became stranger and stranger.

First I will take a moment to note, my development process was not
user-friendly. There was a high cost to check each guess. I had to:

+ Commit a change
+ Deploy to NonProd (~10 minutes total)
+ Run my manual tests
+ Examine CloudWatch logs to find the recorded behavior

Searching CloudWatch is not an easy or reliable way to detect subtle nuances in
configuration changes. Sometimes the test results would not appear at all,
sometimes I would be searching old time frames, sometimes old tests would be
mixed in with the current tests, I was flooded with unrelated logs. It was
bad.

Kludgy as this development cycle was, I was able to suss out WHAT the
behavior was but WHY was proving to be more difficult.

## Questions at Hand

The strange symptom was that my Microservice was getting requests that look
like `$microservice/new/api/update?value=$1$is_args$args`. Ummm what? NGINX is
supposed to uhh INTERPOLATE those money variables?? I should be getting
`?value=mycrazyvalue` not `?value=$1`. And even stranger, i found that if I
swapped the mirror, it worked.

That is, if I mirror a -> b, my values are not parsed. But if I mirrored b ->
a, it would successfully parse the route. This is so weird. But if I wanted to
verify that a -> b didn't work like that, it'd be a 15 wait to deploy and learn
the answer. 

And if I thought, hmm I wonder if a -> b with $request_uri works, when $1
doesn't. And since b -> a fixes $1, does it break $request_uri?  Or does
$request_uri work still? These questions are too numerous, too complicated, and
too subtle to wait 15+ minutes between each time I ask.

## Answers to Find

How to answer these questions? How to answer them in a less painful
way? I had a couple ideas. I could go directly into the NonProd NGINX
server with my changes or I could make a dummy NGINX server in our
network, but both of these were mucking up the environment too much
for my taste. Additionally, this didn't answer the question of getting
better logs of what actually happened.

Then I thought, why not install NGINX on my laptop and run the confs locally?
Lol! As if! NGINX was not happy running on my silly little computer.  It 
is server software and belongs on a server.

So then I thought that it would be smart to use Docker. Here is a winning idea!
But if I load NGINX into Docker, how does it talk to my services? I was sick of
trying to hook into real-world networks and real-world services. There were
too many complications, side effects, and fragile bits. I wanted to isolate the
hell out of the NGINX files. They wanted to squirm away but I was bent on
pinning them down for a good interrogation.

![Interrogation](https://docs-unettest.s3.us-east-2.amazonaws.com/rick+dicker+interrogation.png)

At this point I was only interested in the Monolith and the Microservice as
*interfaces*. I do not care what they do after they have been sent the correct
response. I thought, why not mock them? The only thing that I care about
Monolith is that it's called with `/api/v1/important_update/mycrazyval` and the
only thing I care about Microservice is that it's called at the same time
but with `/new/api/update?value=mycrazyval`. Let's make a mock or two! Mix
yourself a mocktail.

``` yaml
services:
  - monolith:
      routes:
        - name: mirror_me_please
          route: "/api/v1/important_update/<crazyval>/"
          method: "GET"
          status: 200
          params:
            - xml_contents
  - microservice:
      routes:
        - name: place_to_mirror_to
          route: "/new/api/update"
          method: "GET"
          status: 200
          params:
            - crazyval
```

This is a yaml config following a standard I have created for
`unettest`. It tells `unettest` what the network looks like: what
services are on it and what their interfaces look like. Now I can work
against them. I do not care that Monolith also does 10 million other
things. I do not have to support its dependencies. It could be a black
box that I have no control over. It could be a service that is only
available in Production (!!) and can not be engineered against in
NonProd.

Under the hood, `unettest` will parse this valid and complete configuration
file and create two little local webapps conforming to the standard. Their
ports are exposed via localhost. More interesting though, `unettest` also spins
up an NGINX server. You must configure it with NGINX conf files. NGINX is
exposed on `localhost:4999`. If I invoke
`localhost:4999/api/v1/important_update/mycrazyval`, I can see in my
terminal--immediately--what services are called and with what. If I want to
switch a -> b or b -> a, I can edit the NGINX files on my laptop, restart
`unettest`, and immediately see what happens when I curl my little 'network'.

## Tests

If the Mocks we defined above are our Spies, lets use them to observe our
network's behavior.

``` yaml
tests:
  - test_mirror:
      send: "GET"
      target: "/api/v1/important_update/urgent/"
      vars:
        crazyval: urgent
      expect: 
        microservice.place_to_mirror_to:
          called_times: 1
          method: "GET"
          return_status: 200
          called_with:
            params:
              - crazyval
        monolith.mirror_me_please
          called_times: 1
          method: "GET"
          return_status: 200
```

This is a definition of a test that can be run against your network of mocks.

As you can see, it'll run a curl of "/api/v1/important_update/urgent/" against
the internal NGINX server you configured and then assert that the route defined
in the `monolith` server block and `microservice` are called in the ways they
should be called. This information is collected from the within the mocks
themselves. So you know when you run this command, it has run in and out
entirely of the NGINX scripts under test. If your mocks are correctly
configured, you are guaranteed that your route works as you say it does. It is
under test coverage now.

## Takeaway

`unettest` started as a tool for me to put my untested network rules under
locally runnable tests. But I see a lot of ways `unettest` can help you develop
confidently on your laptop and know how things will work in the strange twists
and turns of the internet. You could easily write a lambda plugin (or ask me! I
take feature requests1) to run your lambda on your laptop. Amazon has announced
SAM Local, but everything I've read about it makes it too heavy. It didn't work
well with my current CI setup. I don't want to replace my deployment
infrastructure to run my lambda on localhost. But also it's annoying to write
the specialist AWS infrastructure (hello, specific lambda request
json--`statusCode`, `body`, `content`)
