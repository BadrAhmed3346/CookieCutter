////////////////////////////////
// Setup
////////////////////////////////

// Gulp and package
const { src, dest, parallel, series, watch } = require('gulp')
const pjson = require('./package.json')

// Plugins
const autoprefixer = require('autoprefixer')
const concat = require('gulp-concat')
const cssnano = require ('cssnano')
const imagemin = require('gulp-imagemin')
const pixrem = require('pixrem')
const plumber = require('gulp-plumber')
const postcss = require('gulp-postcss')
const rename = require('gulp-rename')
const sass = require('gulp-sass')(require('sass'))
const spawn = require('child_process').spawn
const uglify = require('gulp-uglify-es').default

// Relative paths function
function pathsConfig(appName) {
  this.app = `./${pjson.name}`
  const vendorsRoot = 'node_modules'

  return {
    bootstrapSass: `${vendorsRoot}/bootstrap/scss`,
    vendorsJs: [
      `${vendorsRoot}/@popperjs/core/dist/umd/popper.js`,
      `${vendorsRoot}/bootstrap/dist/js/bootstrap.js`,
    ],
    app: this.app,
    templates: `${this.app}/templates`,
    css: `${this.app}/static/css`,
    sass: `${this.app}/static/sass`,
    fonts: `${this.app}/static/fonts`,
    images: `${this.app}/static/images`,
    js: `${this.app}/static/js`,
  }
}

const paths = pathsConfig()

////////////////////////////////
// Tasks
////////////////////////////////

// Styles autoprefixing and minification
function styles() {
  const processCss = [
      autoprefixer(), // adds vendor prefixes
      pixrem(),       // add fallbacks for rem units
  ]

  const minifyCss = [
      cssnano({ preset: 'default' })   // minify result
  ]

  return src(`${paths.sass}/project.scss`)
    .pipe(sass({
      includePaths: [
        paths.bootstrapSass,
        paths.sass
      ]
    }).on('error', sass.logError))
    .pipe(plumber()) // Checks for errors
    .pipe(postcss(processCss))
    .pipe(dest(paths.css))
    .pipe(rename({ suffix: '.min' }))
    .pipe(postcss(minifyCss)) // Minifies the result
    .pipe(dest(paths.css))
}

// Javascript minification
function scripts() {
  return src(`${paths.js}/project.js`)
    .pipe(plumber()) // Checks for errors
    .pipe(uglify()) // Minifies the js
    .pipe(rename({ suffix: '.min' }))
    .pipe(dest(paths.js))
}

// Vendor Javascript minification
function vendorScripts() {
  return src(paths.vendorsJs, { sourcemaps: true })
    .pipe(concat('vendors.js'))
    .pipe(dest(paths.js))
    .pipe(plumber()) // Checks for errors
    .pipe(uglify()) // Minifies the js
    .pipe(rename({ suffix: '.min' }))
    .pipe(dest(paths.js, { sourcemaps: '.' }))
}

// Image compression
function imgCompression() {
  return src(`${paths.images}/*`)
    .pipe(imagemin()) // Compresses PNG, JPEG, GIF and SVG images
    .pipe(dest(paths.images))
}

{%- if cookiecutter.use_async == 'y' -%}
// Run django server
function asyncRunServer() {
  const cmd = spawn('gunicorn', [
      'config.asgi', '-k', 'uvicorn.workers.UvicornWorker', '--reload'
      ], {stdio: 'inherit'}
  )
  cmd.on('close', function(code) {
    console.log('gunicorn exited with code ' + code)
  })
}
{%- else %}
// Run django server
function runServer(cb) {
  const cmd = spawn('python', ['manage.py', 'runserver'], {stdio: 'inherit'})
  cmd.on('close', function(code) {
    console.log('runServer exited with code ' + code)
    cb(code)
  })
}
{%- endif %}

// Watch
function watchPaths() {
  watch(`${paths.sass}/*.scss`{% if cookiecutter.windows == 'y' %}, { usePolling: true }{% endif %}, styles)
  watch([`${paths.js}/*.js`, `!${paths.js}/*.min.js`]{% if cookiecutter.windows == 'y' %}, { usePolling: true }{% endif %}, scripts)
}

// Generate all assets
const generateAssets = parallel(
  styles,
  scripts,
  vendorScripts,
  imgCompression
)

// Set up dev environment
const dev = parallel(
  {%- if cookiecutter.use_docker == 'n' %}
  {%- if cookiecutter.use_async == 'y' %}
  asyncRunServer,
  {%- else %}
  runServer,
  {%- endif %}
  {%- endif %}
  watchPaths
)

exports.default = series(generateAssets, dev)
exports["generate-assets"] = generateAssets
exports["dev"] = dev
