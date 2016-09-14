import falcon
import json
import logging
import os
import tempfile
from pygwas.core import ld
from pygwas.core import genotype
from pygwas.core import phenotype
from wsgiref import simple_server
from pygwas import pygwas
import mimetypes
import numpy as np

GWAS_STUDY_FOLDER=os.environ['GWAS_STUDY_FOLDER']
GWAS_VIEWER_FOLDER=os.environ['GWAS_VIEWER_FOLDER']
GENOTYPE_FOLDER=os.environ['GENOTYPE_FOLDER']




class RequireJSON(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='http://docs.examples.com/api/json')

        '''if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='http://docs.examples.com/api/json')'''


class JSONTranslator(object):

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0) or 'application/json' not in req.content_type:
            # Nothing to do
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context['doc'] = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        if 'result' not in req.context:
            return

        resp.body = json.dumps(req.context['result'])


class LdForSnpResource(object):

    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)

    def on_get(self, req, resp,analysis_id,chr,position):
        position = int(position)
        ld_data = ld.get_ld_for_snp('%s/%s.hdf5' % (self.storage_path,analysis_id),chr,position)
        req.context['result'] = ld_data
        resp.status = falcon.HTTP_200

class LdForRegionResource(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)

    def on_get(self, req, resp,analysis_id,chr,start_pos,end_pos):
        start_pos = int(start_pos)
        end_pos = int(end_pos)
        ld_data = _replace_NaN(ld.get_ld_for_region('%s/%s.hdf5' % (self.storage_path,analysis_id),chr,start_pos,end_pos))
        req.context['result'] = ld_data
        resp.status = falcon.HTTP_200

class LdExactForRegionResource(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)

    def on_post(self, req, resp,genotype_id,chr,position):
        #filter nan
        position = int(position)
        genotypeData = genotype.load_hdf5_genotype_data('%s/%s/all_chromosomes_binary.hdf5' % (self.storage_path,genotype_id))
        num_snps = int(req.params.get('num_snps',250))
        accessions =  req.context.get('doc',[])

        ld_data = _replace_NaN(ld.calculate_ld_for_region(genotypeData,accessions,chr,position,num_snps=num_snps))
        req.context['result'] = ld_data
        resp.status = falcon.HTTP_200


class StatisticsResource(object):
    def __init__(self,storage_path):
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)

    def on_post(self,req,resp,genotype_id,type):
        phenotypes =  zip(*req.context.get('doc',[]))
        accessions = phenotypes[0]
        values = phenotypes[1]
        phen_data = phenotype.Phenotype(accessions,values,'phenotype')
        genotype_folder = '%s/%s' % (self.storage_path,genotype_id)
        arguments = {'type':type,'genotype_folder':genotype_folder,'phen_data':phen_data,'file':''}
        statistics = pygwas.calculate_stats(arguments)
        req.context['result'] = statistics
        resp.status = falcon.HTTP_200

class PlottingGwasResource(object):
    def __init__(self,study_path,viewer_path):
       self.study_path = study_path
       self.viewer_path = viewer_path
       self.logger = logging.getLogger(__name__)

    def on_get(self, req, resp,type,id):
        if type not in ('study','viewer'):
             raise falcon.HTTPNotFound()
        file = '%s/%s.hdf5' % (self.viewer_path if type == 'viewer' else self.study_path,id)
        _gwas_plot(file,resp,req)


class PlottingGenericResource(object):
    def __init__(self,plot_func):
        self.logger = logging.getLogger(__name__)
        self.plot_func = plot_func

    def on_post(self,req,resp):
        '''Sending a gwas result file to plot'''
        ext = mimetypes.guess_extension(req.content_type)
        if not ext and req.content_type == 'application/hdf5':
            ext = 'hdf'

        if ext not in ('hdf','csv'):
            raise falcon.HTTPUnsupportedMediaType('Only hdf5 and csv files are supported')
        _,file = tempfile.mkstemp(suffix='.%s' % ext)
        with open(file, 'wb') as f:
            while True:
                chunk = req.stream.read(4096)
                if not chunk:
                    break
                f.write(chunk)
        self.plot_func(file,resp,req)
        os.unlink(file)

class PlottingQQResource(object):
    def __init__(self,study_path,viewer_path):
       self.study_path = study_path
       self.viewer_path = viewer_path
       self.logger = logging.getLogger(__name__)

    def on_get(self, req, resp,type,id):
        if type not in ('study','viewer'):
             raise falcon.HTTPNotFound()
        file = '%s/%s.hdf5' % (self.viewer_path if type == 'viewer' else self.study_path,id)
        format = req.params.get('format','png')
        if format not in ('png','pdf'):
            raise falcon.HTTPUnsupportedMediaType('Only png and pdf formats are supported')
        _qq_plot(file,resp,req)

def _replace_NaN(ld_data):
    ld_data['r2'] = map(lambda x: np.nan_to_num(x).tolist(),ld_data['r2'])
    return ld_data


def _qq_plot(file,resp,req):
    _plot(file,resp,req,pygwas.qq_plot,{})


def _gwas_plot(file,resp,req):
    args = {}
    args['chr'] = req.params.get('chr',None)
    args['macs'] = int(req.params.get('macs',15))
    _plot(file,resp,req,pygwas.plot,args)

def _plot(file,resp,req,plot_func,args):
    format = req.params.get('format','png')
    if format not in ('png','pdf'):
        raise falcon.HTTPUnsupportedMediaType('Only png and pdf formats are supported')
    args['file'] = file
    _,args['output'] = tempfile.mkstemp(suffix='.%s' % format)
    try:
        plot_func(args)
        resp.content_type = 'application/pdf' if format == 'pdf' else 'image/png'
        with open(args['output'],'rb') as f:
            resp.body = f.read()
    except Exception as err:
        raise err
    finally:
        os.unlink(args['output'])

api = falcon.API(middleware=[
    RequireJSON(),
    JSONTranslator(),
])

ldForSnp = LdForSnpResource(GWAS_STUDY_FOLDER)
ldForRegion = LdForRegionResource(GWAS_STUDY_FOLDER)
ldForExactRegion = LdExactForRegionResource(GENOTYPE_FOLDER)
plotting_gwas = PlottingGwasResource(GWAS_STUDY_FOLDER,GWAS_VIEWER_FOLDER)
plotting_gwas_generic = PlottingGenericResource(_gwas_plot)
plotting_qq_generic = PlottingGenericResource(_qq_plot)
plotting_qq = PlottingQQResource(GWAS_STUDY_FOLDER,GWAS_VIEWER_FOLDER)
statistics = StatisticsResource(GENOTYPE_FOLDER)

api.add_route('/analysis/{analysis_id}/ld/{chr}/{position}', ldForSnp)
api.add_route('/analysis/{analysis_id}/ld/region/{chr}/{start_pos}/{end_pos}', ldForRegion)
api.add_route('/ld/{genotype_id}/{chr}/{position}',ldForExactRegion)
api.add_route('/plotting/{type}/{id}/gwas',plotting_gwas)
api.add_route('/plotting/{type}/{id}/qq',plotting_qq)
api.add_route('/plotting/gwas',plotting_gwas_generic)
api.add_route('/plotting/qq',plotting_qq_generic)
api.add_route('/statistics/{genotype_id}/{type}',statistics)

def main():
    httpd = simple_server.make_server('0.0.0.0', 8009, api)
    httpd.serve_forever()

if __name__ == '__main__':
    main()