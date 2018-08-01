About LexaLink
==============

LexaLink is a free open source (Apache Licence-2.0) platform that allows you to setup a dating website or a social network. The LexaLink platform is written in Python and is designed from the ground up to run on the Google App Engine. 

LexaLink Features
=================
* User registration and authentication - sends email to user and provides a secret link to activate their account
* Custom session management
* User defined profiles including text description, photos, and checkbox fields related to their interests
* Efficient searches through profiles based on user-defined search criteria
* One-on-one chat functionality as well as group chat (polling based)
* Management of virtual kisses, winks, etc.
* Ability to mark photos as private and to send a "key" to users that you wish to have access to the photo
* Code for processing paypal payments and awarding VIP status to clients that make a payment
* Multi-lingual (the platform currently works in both Spanish and English)
* Sending email notifications of new messages and of new kisses/winks/etc.
* Captcha verification for users that have been flagged as sending Spam to other users
* Sophisticated logs that notify the administrator of internal errors and unexpected conditions
* Administrator photo-review page for quickly approving or rejecting both public and private photos
* All other functionality required to have a fully functional dating website

Get LexaLink Source Code
========================
You can download the most recent version of LexaLink, the free open-source social network and dating website  platform for the Google App Engine here:
LexaLink.zip

The source code Git repository for LexaLink can be found at: https://github.com/alexander-marquardt/lexalink

Get LexaLink Dependencies
=========================
LexaLink is a Python 2.7 application that runs on the Google App Engine.  In order to run LexaLink, you must have the following programs and files installed:

Google App Engine Launcher (most recent release tested with AppEngine SDK 1.9.4)
Python 2.7
PIL (Python Imaging Library)

Getting started with the Google App Engine
==========================================
It is recomendable that you take some time to understand the Google App Engine and the Python 2.7 runtime environment. 

Running a LexaLink website locally
==================================
Once you have installed LexaLink, the App Engine package, and the required python libraries, you can run LexaLink locally on the App Engine development server with the following command:

    python ./manage.py runserver [localhost:8080]

Where localhost:8000 is optional, and simply defines the name/IP address and port that you will be running your local server at - if you do not enter a value, then the default is localhost:8080.

Browse to http://localhost:8080 (or the value that you have defined) to view your website running on the local/development server.

Organization of the source code
===============================
LexaLink is a complex software package that consists of tens of thousands of lines of computer code. In this section we give a brief overview of the important directories and files within the codebase.

If you would like to browse the codebase without downloading the LexaLink package, please see the source files at https://github.com/alexander-marquardt/lexalink.

Top level
---------
In the LexaLink directory (which we call the "top level" directory) you will see several sub-directories, several files that end with a .yaml extension, and several .py files. 

In general, the .py files at the top level are used for building dependent files, for executing the code, and for uploading the code to the server. The .yaml files are special files required by the App Engine for building indexes, and for providing information to the app engine about the configuration of your project. 

The most important files at this level are manage.py for running the development server. 

There are two important subdirectories:
The rs directory, which contains most of the custom python code in the LexaLink codebase.
The client/app directory contains most of the custom html, css (styles), images, and javascript (scripts) used for running Lexalink.

Directory: "rs"
--------------
Inside the top level directory is a directory called rs (for historical reasons). This is the directory that contains the majority of code that is responsible for running a LexaLink powered website.  If you wish to see which function is called by a given URL, you can view the url_common.py file. 

The file models.py contains the definitions of the data structures that are written to the database.


Directory: "client/app"
----------------------
The client/app directory contains all common css, javascript, and images that are used by the LexaLink platform. There are three main sub-directories within the app directory: 
static- contains css definitions
images- contains images and graphics files
scripts- contains javascript code
html - contains html templates

Directory: "client/app/proprietary"
----------------------------------
This section is only applicable to advanced users that wish build multiple websites from a single codebase. 

The client/app/proprietary directory does not exist in the distributed code base, and can optionally be created manually. This is discussed in more detail in the Custom Configuration section.


Directory: "rs/proprietary"
--------------------------
This section is only applicable to advanced users that wish build multiple websites from a single codebase. 

The rs/proprietary directory does not exist in the distributed code base, and can optionally be created manually. This is discussed in more detail in the Custom Configuration section.

Basic configuration
===================
Select what type of social-network / dating-site you want to run.
-----------------------------------------------------------------
The LexaLink package is designed to allow you to setup various types of social networks and dating websites. Currently, it supports several distinct website formats.
language_build - setup a language exchange site similar to LikeLanguage
discrete_build - setup a discrete dating site similar to RomanceSecreto
single_build - setup a dating website similar to SingletonSearch
lesbian_build - setup a lesbian dating site similar to LesbianHeart
friend_build - setup a "friend search" website similar to FriendBazaar
gay_build - setup a gay dating site similar to GaySetup
mature_build - setup an older contacts site similar to MellowDating

By default, if you are just using the off-the-shelf configuration, the settings for default_build will be used. These are very similar to the single_build settings. 

For each website type that you wish to launch, you will likely want to replace images, logos, and CSS with things that are appropriate for your particular website, as discussed in the Custom Configuration section. 

About app.yaml
---------------
Please read about the App Engine app.yaml file for background information if you are new to the App Engine. 

In order to help us build multiple websites from the same codebase, we automatically run pre-processing scripts to generate a build-specific app.yaml file before running the code locally and before uploading code to the servers. Therefore, we do not directly edit the app.yaml file -- instead, app_generic.yaml acts as a template for app.yaml. The build scripts will incorporate configuration settings defined in site_configuration.py into the app_generic.yaml file in order to generate app.yaml. 

It is unlikely that you will need to edit the app_generic.yaml file, and advisable that you do not modify the app.yaml file (since any modifications will be over-written by the build scripts anyway).

Define the version
------------------
For each application that you have registered on the App Engine, you are permitted to host 10 distinct revisions of your code. This allows you to quickly switch to a known good version in the case that you discover that a particular build is mis-behaving. We define a variable called VERSION_ID in the top-level site_configuration.py file that indicates the name that the current build will be assigned when uploaded to the App Engine server. We use a name with the format 'YYYY-MM-DD-hhmm' for assigning the version name, but you can use whatever name you like (as long as the name  obeys the naming rules for "version" allowed in the app.yaml file).

Enable or disable compressed static files
-----------------------------------------
In the top-level site_configuration.py file, there is a variable called USE_COMPRESSED_STATIC_FILES that indicates that LexaLink should compress and cache-bust all static files.

Using this option requires having node, npm, and grunt installed.  See description of ENABLE_GRUNT in site_configuration.py for more information on this requirement.

Custom configuration
====================
In this section, we give a brief introduction to how you should customize settings that are unique to your websites. 

Private data that you must define
----------------------------------
In the file rs/private_data.py or alternatively in rs/proprietary/my_private_data.py (if you have manually created it by copying the rs/private_data.py file to the rs/proprietary directory) you will specify proprietary data for your LexaLink installation. Most of the fields in the *private_data.py files are well documented in the source code and will not be discussed here, however, we highlight a few important values that must absolutely be defined before you upload your website to the App Engine.

* app_id_dict - each application that you wish to upload to the App Engine will require that you create a unique application identifier at appengine.google.com. Each of these application identifiers should be entered into the app_id_dict for the appropriate site. 
* SECRET_KEY - see the comment in gaesessions/__init__.py regarding cookie_key - should be a random sting of a minimum of 32 bytes. 
* RECAPTCHA_PUBLIC_KEY/RECAPTCHA_PRIVATE_KEY - You must register with reCAPTCHA to get your own keys for use on your website. (Note: it is important that you get these keys, since users that send messages that are marked by other users as "spam" will have to solve a captcha - and if these keys are not correct, they will never pass the captcha test.
* app_name_dict - will contain the name of your website (without .com) - this is mostly used in user messages or emails. For example, for our language exchange website, the 'Language' key would have the value 'LikeLanguage'.
* domain_name_dict - contains the domain name, including the top-level domain. For example, for our language exchange website, the 'Language' key would have the value 'likelanguage.com'.

Custom css and images
---------------------
If you are only planning on running a single website from the code that you have downloaded then you can directly modify the common css and images. 

If you wish to enable the use of proprietary files for your website then you should create an rs/proprietary directory as described in the previous section. We check if this directory exists to determine if we should attempt to use proprietary configuration files.

If you wish to include proprietary configurations, then your build will expect to find the following files in the newly created directory:
* client/app/proprietary/styles/[build_name]_common.css. 
* client/app/proprietary/styles/[build_name]_menubar.css
* client/app/proprietary/styles/proprietary_common.css
You can copy the client/app/styles/default_build*.css file to use as a starting point, and can start a proprietary_common.css file from scratch.

Additionally, you will likely want to create a client/app/proprietary/images directory to store custom images accessed by your proprietary css. 

You will also have to ensure that you have placed your logo in client/app/proprietary/images/[build_name]/[build_name].png (edit the file client/app/html/common_helpers/logo_banner.html if you wish to change the location of the logo).

Uploading LexaLink to the AppEngine
===================================
The easiest way to upload code is to execute: appcfg.py update . 

If you are willing to put a little more effort in, LexaLink comes with automated scripts that will help ensure that static files are properly time-stamped and compressed before being uploaded to the App Engine servers. You will need to have node and npm installed, and make sure that in site_configuration.py you have set the ENABLE_GRUNT and USE_COMPRESSED_STATIC_FILES flags.

Administrative tasks
====================
For the most part, LexaLink-powered websites run themselves, however there are still some administrator tasks that are required to ensure that your website runs smoothly.

Currently, any URL that starts with rs/admin are restricted to administrator users, as defined in your App Engine Permissions. 

Required administrator accounts
-------------------------------
Please note that each LexaLink powered website requires that you have registered google apps accounts  (google apps is not the same as google app engine) for support@domain_name.com, and given administrator permission to this account. 

support@domain_name.com - is the email account that will send out user registration emails and message notifications to users. 

Reviewing and approving photos
------------------------------
LexaLink allows users to mark their photos as either public or private. Public photos will be seen by anyone who views a users profile, while private photos will only be shown to other users that have been authorized by the profile owner. Access to private photos is given by a user giving the "key" to other users. As an administrator, you can review photos that users have marked as public as well as private by accessing the following URLs within your website. 

When reviewing photos, you can elect to only show new photos, which correspond to new photos that you have not yet reviewed. You can also show all photos. 

The URLs for reviewing photos are given below.
* rs/admin/review_public_photos/[show_new | show_all] - review photos that users wish to show as "public" photos
* rs/admin/review_private_photos/[show_new | show_all] - review photos that users wish to display as "private" photos (you may for example allow some nudity for private photos, but not for public photos)

Removing users
--------------
Occasionally, you will find profiles that need to be deleted. We have included special administrator URLs for quickly eliminating un-desirable profiles. The following URL can be used to quickly disable profiles either by username or by IP address.

rs/admin/action/[action-to-take]/[name|email|ip]/profile_to_remove/[reason_for_removal]/

action-to-take: delete, undelete, disable, reset (see code for details)
[name|email|ip]: literally enter "ip", "email", or "name" to indicate how we are selecting the profile to take the action on.
* profile_to_remove: depending on the previous setting, this will be a name, email address, or an ip address.
* reason_for_removal is optional, or can be set to the following values:
  * fake - For profiles that appear to be setup to attract a client to a paid website
  * scammer - For profiles that appear to be "nigerian scammers"
  * terms - For profiles that have violated the terms and conditions of use.
  * Leave this field blank if you do not wish to indicate any reason for removal.

Note: deleted profiles are not physically erases from the database, however we make them in-accessible. Physically erasing deleted profiles is a pending task.

Future enhancements (to-do list)
================================
* Discussion fourms and/or blog capabilities
* Facebook integration
* Mobile apps to integrate with the backend database
* Video conferencing (partially implemented, but not finished)
* Improved chat (ie. a chat that is not polling based)
* Improved photo-upload interface
* Automated algorithms for suggesting profiles that would be a good match for a given user
* Additional languages - currently supports English and Spanish

