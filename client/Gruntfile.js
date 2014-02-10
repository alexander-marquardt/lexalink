// Generated on 2014-01-23 using generator-webapp 0.4.7
'use strict';

// # Globbing
// for performance reasons we're only matching one level down:
// 'test/spec/{,*/}*.js'
// use this if you want to recursively match all subfolders:
// 'test/spec/**/*.js'

module.exports = function (grunt) {

    // Load grunt tasks automatically - reads the dependencies in package.json and loads the matching tasks.
    require('load-grunt-tasks')(grunt);

    // Time how long tasks take. Can help when optimizing build times
    require('time-grunt')(grunt);

    // Define the configuration for all the tasks
    grunt.initConfig({

        // Project settings
        yeoman: {
            // Configurable paths
            app: 'app',
            dist: 'dist',
        },

        build_settings: grunt.file.readJSON('build_settings.json'),

        // Watches files for changes and runs tasks based on the changed files
        watch: {
            gruntfile: {
                files: ['Gruntfile.js']
            },
            js: {
                files: ['<%= yeoman.app %>/scripts/**/*.js'],
                tasks: ['jshint'],
                options: {
                   livereload: true
                }
            },
            styles: {
                files: ['<%= yeoman.app %>/styles/**/*.css'],
                options: {
                   livereload: true
                }
            },
            html: {
                files: ['<%= yeoman.app %>/html/**/*.html'],
                options: {
                   livereload: true
                }
            },
            images: {
                files: ['<%= yeoman.app %>/images/**/*.{gif,jpeg,jpg,png,svg,webp}'],
                options: {
                   livereload: true
                }
            }
        },

        // Empties folders to start fresh
        clean: {
            dist: {
                files: [{
                    dot: true,
                    src: [
                        '.tmp',
                        '<%= yeoman.dist %>/*'
                    ]
                }]
            },
            server: '.tmp'
        },

        // Make sure code styles are up to par and there are no obvious mistakes
        jshint: {
            options: {
                jshintrc: '.jshintrc',
                reporter: require('jshint-stylish')
            },
            all: [
                'Gruntfile.js',
                '<%= yeoman.app %>/scripts/{,*/}*.js',
                '!<%= yeoman.app %>/scripts/vendor/*'
            ]
        },

        // Add vendor prefixed styles
        // ARM - this means that certain css properties that require vendor specific definitions, will
        // be automatically computed from the base css -- i.e.
        // border-radius: 10px 5px;
        // could automatically generate browser specific css such as:
        // -moz-border-radius: 10px 5px;
        // etc..
        autoprefixer: {
            options: {
                browsers: ['last 1 version']
            },
            dist: {
                files: [{
                    expand: true,
                    cwd: '.tmp/styles/',
                    src: '{,*/}*.css',
                    dest: '.tmp/styles/'
                },
                {
                    expand: true,
                    cwd: '.tmp/proprietary/styles/',
                    src: '{,*/}*.css',
                    dest: '.tmp/proprietary/styles/'
                }]
            }
        },

        // Automatically inject Bower components into the HTML file
        'bower-install': {
            app: {
                html: '<%= yeoman.app %>/index.html',
                ignorePath: '<%= yeoman.app %>/'
            }
        },



        // The following plugin is used for searching for and replacing text strings in various files.
        // For the moment, this is used to ensure that the proper build_name is used for different builds.
        replace: {
          dist: {
            options: {
              patterns: [
                {
                  match: /{{\s*build_name\s*}}/g,
                  replacement: '<%= build_settings.build_name %>'
                },
                {
                  match: /{{\s*build_name_used_for_menubar\s*}}/g,
                  replacement: '<%= build_settings.build_name_used_for_menubar %>'
                }
              ],
              usePrefix: false,
              prefix: '' // remove prefix
            },

            files: [
              {expand: true, flatten: true, src: ['<%= yeoman.app %>/html/import_main_css_and_js.html'], dest: './.tmp/'}
            ]
          }
        },

        // Reads HTML for usemin blocks to enable smart builds that automatically
        // concat, minify and revision files. Creates configurations in memory so
        // additional tasks can operate on them
        useminPrepare: {
            options: {
                root: '<%= yeoman.app %>',
                dest: '<%= yeoman.dist %>'
            },
            html: '.tmp/import_main_css_and_js.html'
        },

        // Performs rewrites based on rev and the useminPrepare configuration
        usemin: {
            options: {
                assetsDirs: ['<%= yeoman.dist %>']
            },
            html: ['<%= yeoman.dist %>/html/**/*.html'],
            css: ['<%= yeoman.dist %>/styles/**/*.css']
        },

//        // The following *-min tasks produce minified files in the dist folder
        imagemin: {
            images: {
                files: [{
                    expand: true,
                    cwd: '<%= yeoman.app %>/images/',
                    src: ['{,*/}*.{gif,jpeg,jpg,png}'],
                    dest: '<%= yeoman.dist %>/images/'
                }]
            },
            proprietary_images: {
                files: [{
                    expand: true,
                    cwd: '<%= yeoman.app %>/proprietary/images/',
                    src: '{,*/}*.{gif,jpeg,jpg,png}',
                    dest: '<%= yeoman.dist %>/proprietary/images/'
                }]
            },
            css_images: {
                expand: true,
                dot: true,
                cwd: '<%= yeoman.app %>',
                dest: '<%= yeoman.dist %>',
                src: ['styles/jquery-ui-1.10.3-images/**/*', 'styles/jquery-fancybox-2.1.5-images/**/*']
            },
            build_images: {
                expand: true,
                dot: true,
                cwd: '<%= yeoman.app %>',
                dest: '<%= yeoman.dist %>',
                src: ['images/<%= build_settings.build_name %>/**/*']
            }
        },

        htmlmin: {
            dist: {
                options: {
                    removeComments: true,
                    removeCommentsFromCDATA: true,
                    removeCDATASectionsFromCDATA: true
                },
                files: [{
                    expand: true,
                    cwd: '<%= yeoman.dist %>',
                    src: 'html/**/*.html',
                    dest: '<%= yeoman.dist %>'
                }]
            }
        },


        // Copies remaining files to places other tasks can use
        copy: {
            dist: {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: '<%= yeoman.app %>',
                    dest: '<%= yeoman.dist %>',
                    // images are copied by the imagemin, and styles are copied by the step below
                    src: ['html/**/*', 'proprietary/html/**/*']
//                    src: [
//                        '*.{ico,png,txt}',
//                        '.htaccess',
//                        'images/{,*/}*.webp',
//                        '{,*/}*.html',
//                        'styles/fonts/{,*/}*.*',
//                        'bower_components/' + (this.includeCompass ? 'sass-' : '') + 'bootstrap/' + (this.includeCompass ? 'fonts/' : 'dist/fonts/') +'*.*'
//                    ]
                }]
            },
            styles: {
                expand: true,
                dot: true,
                cwd: '<%= yeoman.app %>/styles',
                dest: '.tmp/styles/',
                src: '{,*/}*.css'
            },
            proprietary_styles: {
                expand: true,
                dot: true,
                cwd: '<%= yeoman.app %>/proprietary/styles',
                dest: '.tmp/proprietary/styles/',
                src: '{,*/}*.css'
            }

        },


        // Renames files for browser caching purposes
        rev: {
            dist: {
                files: {
                    src: [
                        '<%= yeoman.dist %>/scripts/{,*/}*.js',
                        '<%= yeoman.dist %>/styles/{,*/}*.css',
                        '<%= yeoman.dist %>/proprietary/styles/{,*/}*.css',
                        '<%= yeoman.dist %>/images/{,*/}*.{gif,jpeg,jpg,png,webp}',
                        '!<%= yeoman.dist %>/images/*_build/*.{gif,jpeg,jpg,png,webp}', //don't revision the *_build directory since files are accesed from python code.
                        '<%= yeoman.dist %>/styles/fonts/{,*/}*.*',
                        '!<%= yeoman.dist %>/images/unversioned_images/**'
                    ]
                }
            }
        },


        // Run some tasks in parallel to speed up build process
        concurrent: {
            dist: [
                'copy:styles',
                'copy:proprietary_styles',
                'imagemin'
                //'svgmin'
            ]
        }
    });


    grunt.registerTask('serve', function (target) {
        if (target === 'dist') {
            return grunt.task.run(['build', 'connect:dist:keepalive']);
        }

        grunt.task.run([
            'clean:server',
            'autoprefixer',
            'watch'
        ]);
    });

    grunt.registerTask('test', function(target) {
        if (target !== 'watch') {
            grunt.task.run([
                'clean:server',
                'autoprefixer'
            ]);
        }

        grunt.task.run([
            'connect:test',
            'mocha'
        ]);
    });

    grunt.registerTask('build', [
        'clean',
        'replace',
        'useminPrepare',
        'copy',
        'imagemin',
        'autoprefixer',
        'concat',
        'cssmin',
        'uglify',
        'rev',
        'usemin',
        'htmlmin'
    ]);

    grunt.registerTask('default', [
        'newer:jshint',
        'test',
        'build'
    ]);
};
