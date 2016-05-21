import falcon
import json
import logging
import os
from pygwas.core import ld
from pygwas.core import genotype
from wsgiref import simple_server

GWAS_STUDY_FOLDER=os.environ['GWAS_STUDY_FOLDER']
GENOTYPE_FOLDER=os.environ['GENOTYPE_FOLDER']




class RequireJSON(object):
    
    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='http://docs.examples.com/api/json')

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='http://docs.examples.com/api/json')


class JSONTranslator(object):

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
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
        ld_data = ld.get_ld_for_region('%s/%s.hdf5' % (self.storage_path,analysis_id),chr,start_pos,end_pos)
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
        
        ld_data = ld.calculate_ld_for_region(genotypeData,accessions,chr,position,num_snps=num_snps)
        req.context['result'] = ld_data
        resp.status = falcon.HTTP_200
    


api = falcon.API(middleware=[
    RequireJSON(),
    JSONTranslator(),
])

ldForSnp = LdForSnpResource(GWAS_STUDY_FOLDER)
ldForRegion = LdForRegionResource(GWAS_STUDY_FOLDER)
ldForExactRegion = LdExactForRegionResource(GENOTYPE_FOLDER)

api.add_route('/analysis/{analysis_id}/ld/{chr}/{position}', ldForSnp)
api.add_route('/analysis/{analysis_id}/ld/region/{chr}/{start_pos}/{end_pos}', ldForRegion)
api.add_route('/ld/{genotype_id}/{chr}/{position}',ldForExactRegion)

def main():
    httpd = simple_server.make_server('127.0.0.1', 8000, api)
    httpd.serve_forever()

if __name__ == '__main__':
    main()