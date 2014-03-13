from app import app, celery
from app.tasks import retrieve_page, boilerpipe_extract_and_populate
from flask import render_template, flash


@app.route('/')
def welcome():
    return render_template('crawler.html')

@app.route('/initiate_crawl')
def initiate_crawl():
    retrieve_page.delay(app.config['SEED_URL'])
    flash("Crawl: Initiate... (seed: %s)"%(app.config['SEED_URL']))
    return render_template('crawler.html')

@app.route('/pause_crawl')
def pause_crawl():
    celery.control.cancel_consumer("retrieve")
    flash("Crawl: Pause ...")
    return render_template('crawler.html')  

@app.route('/resume_crawl')
def resume_crawl():
    celery.control.add_consumer("retrieve") 
    flash("Crawl: Resume ...")
    return render_template('crawler.html') 

@app.route('/shutdown_crawl')
def shutdown_crawl():
    celery.control.broadcast('shutdown')
    celery.control.purge()
    flash("Crawl: Shutdown ...")
    return render_template('crawler.html')
    
@app.route('/start_bp_extract')
def start_bp_extract():
    boilerpipe_extract_and_populate.delay()
    flash("Boilerpipe: Extraction ...")
    return render_template('crawler.html')

@app.route('/start_jt_extract')
def start_jt_extract():
    flash("jusText: Extraction ...")
    return render_template('crawler.html')