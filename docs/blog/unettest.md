# Network Rules as (Tested) Code

![What is the answer, O Deep Thought](https://docs-unettest.s3.us-east-2.amazonaws.com/o_deep_thought.png)

When we write software, there are many ways to ask a question. We could go to
Stack Overflow or to a smarter coworker, but I like to ask my computer first.
There are many ways to ask computers questions, and one of the most effective is
with TDD. TDD is awesome. We can ask many questions quickly, and once a question
is asked, we can be confident it will remain answered. Given a question on how
something should work, write a test to describe the behavior. Then run the tests
and write code to make the test green. Great stuff. If there is a corner case, a
test case can expose it. When code turns red, make it better.

I was writing NGINX configurations some time ago. I was new to NGINX and trying
to figure it out. Their documentation (lovely though it is) can be impenetrable.
I was grokking the config language by looking at existing configurations and
mimicking what they do. If I had a question, I could not ask it of my computer
easily. NGINX does not have support for unit tests (to my knowledge), or rapid
feedback of any kind. If I want to know the answer to a question, I cannot write
a test and run it locally. I would have to guess and deploy to Staging then wave
around my DevOps dowsing rod to try and sense if things are both working and not
broken. High cost, low reliability.

This is silly but it was working more or less--until I started scratching around
the corners of an NGINX edge case... The only way to figure out what on Earth
was going on was to walk through all the different potential paths of logic, and
ugh, that was not pretty. Let's get into it.

## The Monolith and the Microservice

Here at NYPR, we have a Monolith that does all sorts of things. We are in the
process of excising a part of it to turn into a discrete Microservice with the
goal of eventually recycling enough parts of it to put the whole Monolith down.

We also have a playout system (actually, two) used by our radio team that sends
out an update every few minutes. These requests come through our NGINX server
and are routed to the Monolith. For now and into the foreseeable future, we want
to support both the Monolith and the Microservice running simultaneously. As a
DevOps engineer on staff, I was asked to write a rule in our NGINX configuration
to mirror the requests--they should go to both the Microservice and the
Monolith. This way, the Monolith would continue to work while the Microservice
was under development.

Seems easy enough. Referencing the NGINX docs, we could take the existing rule
and add a `mirror` directive to a special internal location

```
location ~* /api/v1/impotant_update/([^\/]*) {
         proxy_pass $monolith$request_uri;

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
the new API is slightly different from the old one so I need to manipulate it. I
know now (after making `unettest`) that this manipulation was what was the
source of all my fruitless and frustrating NGINX debugging efforts. It seems
that you cannot pass `$1` to the _internal_ location block and parse it like you
would with a regular route. It will be passed literally, as in `?value=$1`
instead of expanding and interpolating the path part. I did not know what was
happening or why at this time.

I fulfilled the requirements (or at least tried to):

+ send incoming request to two servers, (`$monolith`) and (`$microservice`)
+ slightly reconfigure the incoming request to fit the API difference

With that done, I committed my NGINX changes and deployed to Staging.  But... it
did not work. The requests were not being mirrored correctly. The NGINX
documentation, through complete and easy to reference, is anything but beginner
friendly. I thought my conf files were not working due to my own ignorance. I
tried to fix the conf files with that classic development strategy--guess and
check.

But as I guessed and checked, NGINX's behavior became stranger and stranger.

A major hurdle to my progress was my development process. It was not
user-friendly and there was a high cost to check each guess. I had to:

+ Commit a change
+ Deploy to Staging (~10 minutes total)
+ Run my manual tests
+ Examine CloudWatch logs to find the recorded behavior

Searching CloudWatch is not an easy or reliable way to detect subtle nuances in
configuration changes. Sometimes the test results would not appear at all,
sometimes I would be searching old time frames, sometimes old tests would be
mixed in with the current tests, I was flooded with unrelated logs. It was
bad.

It was a bad way of asking questions. This development cycle was so kludgy , I
was able to suss out WHAT the behavior was but not WHY. Not even WHAT EXACTLY.

## An NGINX Corner Case

The strange symptom I observed was that my Microservice was getting requests
that look like `$microservice/new/api/update?value=$1`. Ummm what?  NGINX is
supposed to uhh INTERPOLATE those money variables?? I should be getting
`?value=mycrazyvalue` not `?value=$1`. And even stranger, I found that if I
swapped the mirror, it worked.

That is, if I mirror a -> b, my values are not parsed. But if I mirrored b -> a,
it would successfully parse the route. This is weird. But if I wanted to verify
that a -> b worked or did not, it would be a 15 wait to deploy and learn the
answer.

And if I thought, hmm I wonder if a -> b with `$request_uri` works, when `$1`
doesn't. And since b -> a fixes `$1`, does it break `$request_uri`? Or does
`$request_uri` work still? These questions are too numerous, too interconnected,
and too subtle to wait 15+ minutes between each time I ask. [1]

Why? Why is NGINX behaving like this? Why? Why? Why? NGINX was not giving me
easy answers. The answers I was getting were half-answers (mirrors go unlogged
by default) and they were hard to find. By the time I found an answer, I had
forgotten my question ("umm was $1 used here or was it being redirected in this
one?"). The differences were subtle, the moving pieces were many, and I was
getting frustrated.

## A Better Way to Ask Questions

How to answer these questions? How to ask them in a less painful way? I could go
with my changes directly into the Staging NGINX server or else I could add a
dummy/test NGINX server to our network but both of these were mucking up the
environment too much for my taste. Additionally, this did not give me better
logs or analysis of what happened.

Then I thought to install NGINX on my computer and run the confs locally. Lol!
As if! NGINX was not happy running on my silly little laptop. It is server
software and belongs on a server.

Then I thought to use Docker. Here is a winning idea! But if I load NGINX into
Docker, how would it talk to my services? I was sick of trying to hook into
real-world networks and real-world services. There were too many complications,
side effects, and fragile bits. I wanted to rigorously isolate my NGINX files.
They wanted to squirm away. I was bent on pinning them down for interrogation.

![Interrogation](https://docs-unettest.s3.us-east-2.amazonaws.com/rick+dicker+interrogation.png)

At this point we are only interested in the Monolith and the Microservice
abstractly, as **interfaces**. We do not care what these services do after they
have been sent the correct request (that's a side effect). Only that they _have_
been sent the correct request.

Why not mock them?

The only thing matters about Monolith here is that it is called with
`/api/v1/important_update/mycrazyval` and the only thing important about the
Microservice is that it is invoked at the same time but with
`/new/api/update?value=mycrazyval`.

If we were writing code, we would mock these external systems. Why should
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

This yaml config follows a standard I have created for a test framework I wrote
called [`unettest`](http://unettest.net), a test harness for NGINX, APIs, and
online services.

This yaml config tells `unettest` what the network looks like: what services are
on the network and what their interfaces look like. Now we can develop
confidently against them.

Things we do not have to worry about:

+ that Monolith does 10 million other things
+ what Monolith or Microservice does when these particular endpoints are invoked
+ that Microservice is a Lambda or that Monolith is a legacy pile of spagetti
+ what Monolith's dependencies and requirements are beyond the scope of its public
interface
+ that these might be black-box services that cannot be controlled or might (!!)
be only available in Production environments 

Under the hood, `unettest` will parse this valid and complete configuration file
and create two little local containerized web services conforming to these
definitions. They are not functional, but they behave as if they are and their
behavior is monitored by `unettest`. Their ports are exposed via localhost. More
interesting though, `unettest` also spins up an NGINX server. You must configure
it with NGINX conf files. NGINX is exposed on `localhost:4999`.

If I invoke

`localhost:4999/api/v1/important_update/mycrazyval`

I can see in my terminal immediately which services are called and how they are
called. If I want to switch a -> b or b -> a, I can edit the NGINX files on my
laptop, refresh `unettest`, and immediately see what happens when I curl my
little "network".

## Unit Tests

The Mocks we defined above are Spies; let's use them to observe our network's
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

This is a definition of a test that can be run against the network of mocks.

It will curl `"/api/v1/important_update/urgent/"` against the you configured
internal NGINX server and then assert that the route defined in the `monolith`
server block and `microservice` are called in the ways they should be called.
This information is collected from the within the mocks themselves. So we feel
safe knowing that when we run these tests, they have run in and out of the NGINX
scripts under test. If the mocks are correctly configured, the route is
guaranteed to work as it says it does. It is under test coverage now.

## Take away

![mechanic](https://docs-unettest.s3.us-east-2.amazonaws.com/mechanic.jpg)

`unettest` started as a tool for me to put my untested network rules under
locally runnable tests. But I see a lot of ways `unettest` can help you develop
confidently on your laptop and know how things will work in the strange twists
and turns of the Internet, networks, and production environments. You could
easily write a lambda plugin (or ask me! I take feature requests!) to run your
lambda on your laptop. Amazon has announced SAM Local, but what I've read, it
looks too heavy for me. It didn't work well with my current CI setup.  I don't
want to replace my deployment infrastructure to run a lambda on localhost. But
also it is annoying to write around the specialist AWS infrastructure (hello,
lambda specific request json--`statusCode`, `body`, `content`) just to run a
service. `unettest` can jack up your Lambda or NGINX configuration or anything
else into a test harness so you can easily get under the hood of your network.
See how things really work in the isolated safety of your local dev setup. u got
a network? u net test.


[1] So... what's the verdict on that weird NGINX behavior? I isolated things
in `unettest` and it looks to me that if you pass a `$1` to an internal mirror,
it will not evaluate/expand it. But `$request_uri` works from both the mirror and
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
