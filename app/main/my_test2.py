from  . import main

@main.route('/justtest')
def justtest():
    return 'test success!'