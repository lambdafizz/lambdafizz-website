Title: Is Android's New Build System Production Ready?
Subtitle: ... or are we still stuck with Eclipse and Ant?
Author: Karol Majta
Date: 2014-01-19 13:35
Tags: Java, Android, Gradle

We've been pretty psyched about Android Studio and Gradle ever since it's showcase
at Google I/O 2013. Not giving it much thought we dived into when Android Studio
was at version 0.2.+. And we backed off even faster. The solution was immature and
painful to work with. Since then we've been watching the tooling evolve, but this
time with much more skepticism.

## Know your rights, all three of them…

When introducing automated builds into your workflow, there are at least three
things that you can expect of your tools. In essence:

- They should keep easy things easy, and make hard things possible. You should
  not be forced to write a custom module to copy files or modify classpath.
- The builds should be fast, and **repeatable**.
- Builds should work same way on developers' machines as they do on CI servers.
  In other words, the build script should be part of every developers workflow.

When faced with a project consisting of an android library (which is an actual
product), and a demo app (that allows our client to test the library) we decided
to give Gradle and Android Studio a second chance.

## Batteries included (to some extent…)

There are already some pretty handy android tools aiding testing that come
bundled with Gradle's `android` and `android-library` plugins. Task
`connectInstrumentTest` allows running UI integration tests on connected
devices, as well as unittests. Unfortunately all tests are run on devices,
even if they only touch POJOs and problem domain, and could be easily run
on JVM with JUnit. Fortunately writing custom `unit` task that did exactly
this was quite easy.

There's also a `lint` task that will produce some warnings about your code.
That's nice!

Next thing we needed was the ability to build a library (we went for the
`aar` format because we are pretty sure we will need resources at some point).
This means we are talking about a multi-project build - one subproject for
the library and one subproject for an app utilising it. Actually, inability
to properly configure a multi-project build was the reason we dropped the new
build system last time, so we were pretty amazed that, this time it kind-of
worked from scratch.

Yay, we've got our library, and an app, but they're blissfuly unaware of
each other, happily producing their artifacts. We needed a way to put
the produced `aar` archive into the app's classpath. Should be dead easy,
right? Nope. After some googling we found a mailing list message that
stated:

> This is not yet supported.
	
Are you kidding me? Things like this are the reason word *Java* gives
most people an anti-boner. Putting an `aar` from local filesystem on a
classpath should be the simplest of things!

After a moderately long period of swearing we found that the solution
was to add a library subproject into `dependencies` inside a `compile`
declaration. This is not a cleanest solution, as it will not add
an `aar` file to classpath. Instead it will compile and add the
library's `class` folder and bundle with the resulting `apk`. 

And we finally made it! We have a working multi project build with
proper (but not great) support for automated testing.

## Code Briefing

You can find this app's template at <https://github.com/karolmajta/ExampleAndroidProject>

Let's look at the project's structure:

    :::console
    .
    ├── HelloIdeaApp
    │   ├── build.gradle
	│   └── src
	│       ├── instrumentTest
	│       │   └── java
	│       │       └── TestSomethingInUI.java
	│       ├── main
	│       │   ├── AndroidManifest.xml
	│       │   ├── ic_launcher-web.png
	│       │   ├── java
	│       │   │   └── com
	│       │   │       └── karolmajta
	│       │   │           └── helloideaapp
	│       │   │               └── MainActivity.java
	│       │   └── res
	│       └── unit
	│           └── java
	│               └── TestSomething.java
	├── HelloIdeaLib
	│   ├── build.gradle
	│   └── src
	│       ├── instrumentTest
	│       │   └── java
	│       │       └── TestSomethingInUI.java
	│       ├── main
	│       │   ├── AndroidManifest.xml
	│       │   ├── java
	│       │   │   └── com
	│       │   │       └── karolmajta
	│       │   │           └── helloidealib
	│       │   │               └── HelloIdeaBaseActivity.java
	│       │   └── res
	│       └── unit
	│           └── java
	│               └── TestSomething.java
	├── build.gradle
	├── gradle
	│   └── wrapper
	│       ├── gradle-wrapper.jar
	│       └── gradle-wrapper.properties
	├── gradlew
	├── gradlew.bat
	├── local.properties
	└── settings.gradle

In the root dir we have `local.properties` that just point the Android SDK directory,
Gradle Wrapper files and `settings.gradle` with very simple content (just stating
the subprojects):

	:::groovy
	include ':HelloIdeaLib', ':HelloIdeaApp'

Project-wide `build.gradle` is empty, but it's a good place to override global `build`
command, so that your IDE with Gradle plugin doesn't get dizzy.

Ok, we'll now take a look at `build.gradle` located in `HelloIdeaLib` subproject:

	:::groovy
	buildscript {
	    repositories {
	        mavenCentral()
	    }
    	dependencies {
        	classpath 'com.android.tools.build:gradle:0.6.+'
    	}
	}
	apply plugin: 'android-library'
	apply plugin: 'maven-publish'
	
	repositories {
    	mavenCentral()
	}
	
	android {
    	compileSdkVersion 19
    	buildToolsVersion "19.0.1"

    	defaultConfig {
        	minSdkVersion 7
        	targetSdkVersion 19
        	versionCode 1
        	versionName '0.0.1'
    	}
	}

	dependencies {
    	compile 'com.android.support:appcompat-v7:+'
	}

	/*
 	 * JUnit test support
 	 */

	// extend the runtime
	configurations {
    	unitCompile.extendsFrom runtime
    	unitRuntime.extendsFrom unitCompile
	}

	// add to dependancies
	dependencies {
    	unitCompile files("$project.buildDir/classes/release")
    	unitCompile 'junit:junit:4.11'
	}

	// add a new unit sourceSet
	sourceSets {
    	unit {
        	java.srcDir file('src/unit/java/**')
        	resources.srcDir file('src/unit/resources/**')
    	}
	}


	// add the unit task
	task unit(type:Test, dependsOn: assemble) {
    	description = "run unit tests"
    	testClassesDir = project.sourceSets.unit.output.classesDir
    	classpath = project.sourceSets.unit.runtimeClasspath
	}

	// bind to check
	check.dependsOn unit

At the top we add `android-library` plugin, which is the default for android libraries,
and `maven-publish` that provides `publishToMavenLocal` task. Then comes the ol' boring
stuff - android configuration and dependencies. Next block (JUnit test support) adds
a `unit` task that runs domain-logic test with JUnit and JVM. These tests are located in
the `unit` directory. Then we define how the artifacts should be published. This is
pretty self-explanatory - just publish the generated `aar` file to local maven repo.

This allows us to build and publish artifacts with simple command:

	:::console
	./gradlew :HelloIdeaLib:clean :HelloIdeaLib:build :HelloIdeaLib:publishToMavenLocal
	
`build.gradle` in `HelloIdeaApp` is very similar to the previous one, so we'll just focus
on one important difference:

	:::groovy
	dependencies {
    	compile 'com.android.support:appcompat-v7:+'
    	compile project(':HelloIdeaLib')
	}

The library project is declared as source dependency (bummer, but works for now).

And that's basically it folks.

## Are we there yet?

Is the new build system mature enough for production use? We truly hope so,
and well… if you're planning to run Android builds on a CI server it's
much easier to grasp than Ant.

There's still much room for improvement. Firstly there is no official support
for robolectric. This should change with robolectric-2.3, so we're definately
anticipating the update.

Jar files, next to apklib format, next to aar files cause lots of confusion.
Moreover aar is currently not supported by Eclipse plugin, so you're either
forced to use Android Studio, or publish dependencies to your local maven
repo. That sounds like an overkill, and definately should be fixed.

Support for plugins that are first class citizens on JVM like `checkstyle`
would be a great next step.

So, we're almost there...
