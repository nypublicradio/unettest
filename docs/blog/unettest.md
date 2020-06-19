# Network Rules as (Tested) Code

![What is the answer, O Deep Thought](https://s3.amazonaws.com/unettest.net/assets/o_deep_thought.png)

Sometimes as developers, we start a ticket thinking it will be easy. Sometimes
it turns out to be not easy. The natural thing to do is to reach for our trusted
tools, those reliable methods and strategies for digging ourselves out of holes
like this. And sometimes, those tools are missing.

So we roll our own.

A few months ago, I wanted to write NGINX configurations. I was new to NGINX and
working to figure it out. Their documentation (though lovely) is impenetrable. I
grokked the NGINX config language by mimicking existing configurations but if I
had a question about how NGINX might behave, it was hard to discover the answer
on my own. NGINX does not have support for a usably interactive local
environment or rapid feedback of any kind. If I want to know how some potential
solution works, I would need to deploy it to Staging and then wave around my
DevOps Dowsing Rod to try and sense if things are both working and not broken.
This method was tediously slow and unreliable.

When I write software, there are many ways to ask a question about how things
work or about how they might work. I often go to Stack Overflow or to a smarter
coworker, but I love to ask my computer first. There are many ways to ask
computers questions, and one of the most effective is by TDD. TDD is the cat's
pajamas! We can ask many questions quickly, and once a question is asked, we can
be confident it will remain answered. Given a question on how something should
work, write a test to describe the behavior. Run the tests and write code to
make it green. Great stuff. If there is a corner case, a test case can expose
it. When code turns red, make it better.

I got by without my usual tools, i.e. TDD, until I started scratching around the
corners of an NGINX edge case... The only way to figure out what on Earth was
going on was to walk through all the different potential paths of logic in these
network configuration files, and ugh, that was not pretty. Things that I would
assume to work one way were behaving in entirely different ways. There was no
way to get a certain answer about how things were or were not working.

Until I wrote [`unettest`](http://unettest.net).

## The Monolith and the Microservice

Here at NYPR, we have a Monolith that does all sorts of things. We are in the
process of excising a part of it to turn into a discrete Microservice with the
goal of eventually recycling enough parts of it to put the whole Monolith down.

We have a playout system used by our radio team that sends out an update every
few minutes. These requests come through our NGINX server and are routed to the
Monolith. For now and into the foreseeable future, we want to simultaneously
support the Monolith and the Microservice. As a DevOps engineer on staff, I was
asked to write a rule in our NGINX configuration to mirror the requests: they
should go to both the Microservice and the Monolith.  This way, the Monolith
would continue to work while the Microservice was under development.

Seems easy. Referencing the NGINX docs, we could take the existing rule and add
a `mirror` directive to a special `internal` location block.

```
location ~* /api/v1/impotant_update/([^\/]*) {
         proxy_pass $monolith$request_uri; # original behavior

         mirror /microservice_mirror/$1; # NEW LINE!

         ...some other configurations
}
```

and then define the mirror route like this

```
location ~* /microservice_mirror/(.*) {
         internal;
         proxy_pass $microservice/new/api/update?value=$1;

         ...some other configurations
}
```

> Note: I am trying to do a little funny business with the `$1`. The format of
the new API is slightly different from the old one so I need to manipulate it.
I know now (after making `unettest`) that this manipulation was the source of
my NGINX pain. It seems that you cannot pass `$1` to the _internal_ location
block and parse it like you would with a regular route. It will be passed
literally, as in `?value=$1` instead of expanding and interpolating the path. I
did not know why this was happening or why it only happened sometimes.

I fulfilled the requirements (or at least tried to):

+ send incoming request to two servers, (`$monolith`) and (`$microservice`)
+ slightly reconfigure the incoming request to fit the API difference

With that done, I committed my NGINX changes and deployed to Staging. But... it
did not work. The requests were not being mirrored correctly. The NGINX
documentation, through complete and easy to reference, is not beginner friendly.
I thought my conf files were malfunctioning due to my own ignorance when it
really turned out to be a bug(?) or undefined behavior(?) in NGINX itself but I
did not know this at the time. Lacking my normal tools that I use to learn
unfamiliar technologies (tests!), I tried to fix the conf files with that
classic fallback development strategy--guess and check.

But as I guessed and checked, NGINX's behavior became stranger and stranger.

A major hurdle to my progress was the development process. It was not
user-friendly. It was user-hostile. There was a high cost to check each guess. I
had to:

+ Commit a change
+ Deploy to Staging (~15 minutes wait)
+ Run my manual tests
+ Wade through CloudWatch logs to find the recorded behavior

Searching CloudWatch is not an easy or reliable way to detect subtle nuances in
configuration changes. Often, the test results would not appear at all, I would
be searching old time frames, or old tests would be mixed in with the current
tests. I was flooded with unrelated logs.

It was a bad way of asking questions. This development cycle was so kludgy , I
was able to suss out WHAT the behavior was but not WHY. Not even WHAT EXACTLY.

## An NGINX Corner Case

The strange symptom I observed was that my Microservice was getting requests
that look like `$microservice/new/api/update?value=$1`. What?  NGINX is
supposed to INTERPOLATE the money variables?? I should be getting
`?value=mycrazyvalue` not `?value=$1`. Even stranger, I found that if I swapped
the mirror, it worked.

That is, when mirroring a -> b, the values do not get parsed. Mirroring b -> a
would successfully parse the route. Weird. However, if I wanted to verify that
x -> y worked or did not work, it would be a 15 minute deployment's wait to
learn the answer.

I wondered, if a -> b has a working `$request_uri` and broken `$1`, does b -> a
fix `$1`? Does b -> a break `$request_uri`? Or does `$request_uri` still work?
Does `$1` and `$request_uri` break in the same context? What conditions cause
`$1` to break? Are there conditions that similarly break `$request_uri`? These
questions were too numerous, too interconnected, and too subtle to wait 15+
minutes between each time I ask. [1]

I kept coming back to the question, "Why?" Why is NGINX behaving like this?
NGINX was not giving easy answers. The answers I got were half-answers (mirrors
go unlogged by default) and they were hard to find. By the time I found an
answer, I had forgotten my question ("was $1 used here or was it being
redirected in this one?"). The differences were slight, the moving pieces were
many, and I was getting frustrated.

## A Better Way to Ask Questions

How to answer these questions? How to ask them in a less painful way? 

How to experiment iteratively and informatively on an NGINX configuration with a
learner's mindset? How to do so quickly? One option would be to load changes
directly into the Staging NGINX server. Another way could be adding a dummy/test
NGINX server to the network. These are not good solutions--they muck up the
nonprod environment too much. More importantly, they do not give better
logs or analysis or insight into what is happening.

Another idea would be to run NGINX locally. This seems like a prime candidate
for the [Works On My Machine](https://blog.codinghorror.com/the-works-on-my-machine-certification-program/) certification. It is a dubious solution. NGINX is server 
software and should be running on servers.

This sounds like a great fit for docker! But if we shove the NGINX files into
docker, how would NGINX talk to services on the internet?

I was sick of trying to hook into real-world networks and real-world services.
There were too many complications, side effects, and fragile bits. I wanted to
rigorously isolate the NGINX files.  They wanted to squirm away. I was bent on
pinning them down for interrogation.

![Interrogation](https://s3.amazonaws.com/unettest.net/assets/rick_dicker_interrogation.png)

Looking at it from inside NGINX, the Monolith and the Microservice are being
referenced abstractly, as **interfaces**. It does not matter what these services
do when they have been sent the correct request (that's a side effect). The
crucial thing is that they _have_ been sent the correct request and that they
return a certain response.

Why not mock them?

The only thing that matters about Monolith is that it is called with
`/api/v1/important_update/mycrazyval` and the only important thing about
Microservice is that it is invoked at the same time, but with
`/new/api/update?value=mycrazyval`.

If we were writing code, we would mock those external systems. Why should
network rules be exempt? Let's Mock those services!

``` yaml
services:
  - monolith:
      routes:
        - name: mirror_me_please
          route: "/api/v1/important_update/<crazyval>/"
          method: "GET"
          status: 200
  - microservice:
      routes:
        - name: place_to_mirror_to
          route: "/new/api/update"
          method: "GET"
          status: 200
          params:
            - crazyval
```

This yaml config follows a standard I have created for the test framework I
wrote called [`unettest`](http://unettest.net), a test harness for NGINX, APIs, and online services.

This yaml config tells `unettest` what the network looks like: what services are
on the network and what their interfaces look like. Now we can develop
confidently against them.

Things that do not matter:

+ that Monolith does 10 million other things
+ what Monolith or Microservice does when these particular endpoints are invoked
+ that Microservice is a Lambda or that Monolith is a legacy pile of spaghetti
+ what Monolith's dependencies and requirements are
+ that these might be black-box services that cannot be controlled or might (!!)
be only available in Production environments 

Under the hood, `unettest` parses this valid and complete configuration file and
creates two little local containerized web services conforming to their
definitions. They are not functional, but they behave as if they are and their
behavior is monitored by `unettest`. Their ports are exposed via localhost. More
interesting though, `unettest` spins up an NGINX server. It must be configured
with NGINX conf files. NGINX is exposed on `localhost:4999`.

If I invoke

`localhost:4999/api/v1/important_update/mycrazyval`

I can see in my terminal immediately which services are called and how they are
called. If I want to switch a -> b or b -> a, I can edit the NGINX files on my
laptop, refresh `unettest`, and immediately see what happens when I curl my
little network.

## Unit Tests

The Mocks we defined above are Spies; they can be used to observe the network's
behavior.

``` yaml
tests:
  - test_mirror:
      send: "GET"
      target: "/api/v1/important_update/urgent/"
      vars:
        crazyval: urgent
      expect: 
        - microservice.place_to_mirror_to:
          called_times: 1
          method: "GET"
          return_status: 200
          called_with:
            params:
              - crazyval
        - monolith.mirror_me_please:
          called_times: 1
          method: "GET"
          return_status: 200
```

This is a definition of a test that can be run against the network of Mocks.

It will curl `"/api/v1/important_update/urgent/"` against the configured
internal NGINX server and then assert that the route defined in the `monolith`
server block and `microservice` are called in the ways they should be called.
This information is collected from the within the Mocks themselves so we can
feel safe knowing that when we run these tests, they have run all the way in and
out of the NGINX scripts under test. If the Mocks are correctly configured, the
route is guaranteed to work as it says it does. It is now under test coverage.

## Takeaway

![mechanic](https://docs-unettest.s3.us-east-2.amazonaws.com/mechanic.jpg)
`unettest` started as a tool for me to put my untested network rules under
locally runnable tests. But I see a lot of ways `unettest` can help you develop
confidently on your own computer and know how things will work in the strange
twists and turns of the Internet. Networks, servers, and production environments
are now just interfaces to be worked against.

You could easily write a lambda plugin (or ask me! I take feature requests!) to
run a lambda on your laptop. AWS has announced SAM Local, but from what I've
read, it looks too heavy for what I need. It does not work well with our
existing CI setup. I don't want to replace my deployment infrastructure just to
run a lambda on localhost. But also it is annoying to write around the
specialist AWS infrastructure (hello, lambda specific request json --
`statusCode`, `body`, `content`) in order to run a service on localhost.

`unettest` can jack up a Lambda or an NGINX configuration or anything else into
a test harness so you can easily get under the hood of your network. You can see
how things work in the cloud from the isolated safety of your local dev
environment. u got a network? u net test.

---

If you want to get started with unettest, check out the website and documentation at [unettest.net](http://unettest.net). There is a [tutorial](http://unettest.net/tutorial.html)! Please reach out to me personally if you have trouble or questions. `unettest` is really a high-functioning beta. Send me bug reports! Feature requests! Whatever you need.

<br>

[1] So... what's the verdict on that weird NGINX behavior? I isolated things
in `unettest` and it looks like if you pass a `$1` to an internal mirror,
it will not evaluate/expand it. However, `$request_uri` works from both the mirror and
parent block. Always. 

`$1` cannot be accessed directly from the mirror as if it is in scope,
`$request_uri` can be accessed as if it is in scope. 

You can pass a literal into `(.*)` in the location line--it will receive that
value and parse it into a local (mirror) `$1`. That is, `mirror
/microservice_mirror/LITERAL` will be received by `location ~*
/microservice_mirror/(.*)` and parse out `LITERAL` into the `$1` value.

But if you try to pass in `$1` from the parent block, it remains `$1` in the
mirror, as if you passed it the string literal `"$1"`. I think. Like I said, I
am still an NGINX beginner.
