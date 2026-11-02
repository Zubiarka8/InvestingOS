import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib import error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from InvestingOS import open_sources as o  # noqa: E402


def reply(data):
    body = data if isinstance(data, bytes) else json.dumps(data).encode()
    return io.BytesIO(body)


def run(func, payloads, *args, **kwargs):
    """Call an adapter with canned responses; returns (result, urls requested)."""
    payloads = payloads if isinstance(payloads, list) else [payloads]
    with patch('urllib.request.urlopen', side_effect=[reply(p) for p in payloads]) as opened:
        result = func(*args, **kwargs)
    return result, [call.args[0].full_url for call in opened.call_args_list]


ATOM = b'''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
<entry><id>http://arxiv.org/abs/1810.09869v3</id><title>Religion and
 Terrorism</title><published>2020-03-05T22:23:01Z</published><summary> We study   Ramadan. </summary>
<author><name>A One</name></author><author><name>B Two</name></author>
<link href="https://arxiv.org/abs/1810.09869v3" rel="alternate"/><link href="https://arxiv.org/pdf/1810.09869v3" rel="related"/>
<arxiv:doi>10.1/x</arxiv:doi></entry></feed>'''


class AdapterTests(unittest.TestCase):
    def check_common(self, results, source, kind):
        self.assertTrue(results)
        for item in results:
            self.assertEqual(item['source'], source)
            self.assertEqual(item['kind'], kind)
            self.assertEqual(item['status'], 'unverified')

    def test_europepmc_marks_preprints_and_strips_markup(self):
        data = {'resultList': {'result': [
            {'id': 'PPR1', 'source': 'PPR', 'doi': '10.1/p', 'title': 'A <i>study</i>', 'authorString': 'Smith J, Lee K.',
             'pubYear': '2026', 'firstPublicationDate': '2026-01-02', 'abstractText': '<h4>Aim</h4> Text',
             'isOpenAccess': 'Y', 'pubTypeList': {'pubType': ['Preprint']}}]}}
        results, urls = run(o.europepmc, data, 'fasting', 1, preprints=True)
        self.check_common(results, 'Europe PMC', 'preprint')
        self.assertEqual(results[0]['title'], 'A study')
        self.assertEqual(results[0]['authors'], ['Smith J', 'Lee K'])
        self.assertEqual(results[0]['abstract'], 'Aim Text')
        self.assertEqual(results[0]['url'], 'https://europepmc.org/article/PPR/PPR1')
        self.assertIn('SRC%3APPR', urls[0])

    def test_arxiv_parses_atom_and_combines_plain_words(self):
        results, urls = run(o.arxiv, ATOM, 'intermittent fasting', 1)
        self.check_common(results, 'arXiv', 'preprint')
        self.assertEqual(results[0]['title'], 'Religion and Terrorism')
        self.assertEqual(results[0]['authors'], ['A One', 'B Two'])
        self.assertEqual(results[0]['url'], 'https://arxiv.org/abs/1810.09869v3')
        self.assertEqual(results[0]['published'], '2020-03-05')
        self.assertEqual(results[0]['abstract'], 'We study Ramadan.')
        self.assertIn('all%3Aintermittent+AND+all%3Afasting', urls[0])
        _, urls = run(o.arxiv, ATOM, 'ti:fasting', 1)
        self.assertIn('search_query=ti%3Afasting', urls[0])

    def test_doaj_plos_inspire_zenodo_datacite(self):
        doaj = {'results': [{'id': 'abc', 'bibjson': {'title': 'T', 'author': [{'name': 'N'}], 'year': '2021',
                'journal': {'title': 'J'}, 'identifier': [{'type': 'eissn', 'id': '1'}, {'type': 'doi', 'id': '10.1/d'}],
                'link': [{'url': 'https://example.org/a'}], 'abstract': 'Abs'}}]}
        r, _ = run(o.doaj, doaj, 'fasting', 1)
        self.check_common(r, 'DOAJ', 'article')
        self.assertEqual((r[0]['doi'], r[0]['journal'], r[0]['url']), ('10.1/d', 'J', 'https://example.org/a'))

        plos = {'response': {'docs': [{'id': '10.1371/journal.pone.1', 'title': 'T', 'author_display': ['A', 'B'],
                'journal': 'PLoS ONE', 'publication_date': '2013-06-03T00:00:00Z', 'abstract': ['One', 'Two']}]}}
        r, _ = run(o.plos, plos, 'x', 1)
        self.assertEqual((r[0]['published'], r[0]['abstract'], r[0]['url']),
                         ('2013-06-03', 'One Two', 'https://doi.org/10.1371/journal.pone.1'))

        inspire = {'hits': {'hits': [{'id': '2181837', 'metadata': {'titles': [{'title': 'HZZ'}],
                   'authors': [{'full_name': 'Lu, Y'}], 'preprint_date': '2022-11-14',
                   'arxiv_eprints': [{'value': '2211.07478'}], 'dois': [{'value': '10.1/h'}]}}]}}
        r, _ = run(o.inspire, inspire, 'higgs', 1)
        self.assertEqual((r[0]['doi'], r[0]['arxiv_id'], r[0]['url']), ('10.1/h', '2211.07478', 'https://inspirehep.net/literature/2181837'))

        zen = {'hits': {'hits': [{'doi': '10.5281/z.1', 'links': {'self_html': 'https://zenodo.org/records/1'},
               'metadata': {'title': 'Z', 'creators': [{'name': 'C'}], 'publication_date': '2022-09-30',
                            'resource_type': {'title': 'Dataset'}, 'license': {'id': 'cc-by-4.0'}}}]}}
        r, _ = run(o.zenodo, zen, 'x', 1)
        self.check_common(r, 'Zenodo', 'deposit')
        self.assertEqual((r[0]['resource_type'], r[0]['license']), ('Dataset', 'cc-by-4.0'))

        dc = {'data': [{'id': '10.1/dc', 'attributes': {'titles': [{'title': 'D'}], 'creators': [{'name': 'E'}],
              'publicationYear': 2010, 'publisher': 'Uni', 'url': 'http://example.org/d', 'types': {'resourceTypeGeneral': 'Text'}}}]}
        r, urls = run(o.datacite, dc, 'x', 1)
        self.assertEqual((r[0]['published'], r[0]['publisher'], r[0]['doi']), ('2010', 'Uni', '10.1/dc'))
        self.assertIn('page%5Bsize%5D=1', urls[0])

    def test_clinicaltrials_osf_eric_zbmath(self):
        ct = {'studies': [{'hasResults': True, 'protocolSection': {
            'identificationModule': {'nctId': 'NCT1', 'briefTitle': 'Trial'},
            'statusModule': {'overallStatus': 'COMPLETED', 'startDateStruct': {'date': '2015-09'}},
            'sponsorCollaboratorsModule': {'leadSponsor': {'name': 'Hospital'}},
            'designModule': {'studyType': 'INTERVENTIONAL'}}}]}
        r, _ = run(o.clinicaltrials, ct, 'x', 1)
        self.check_common(r, 'ClinicalTrials.gov', 'registry record')
        self.assertEqual((r[0]['nct_id'], r[0]['overall_status'], r[0]['has_results'], r[0]['url']),
                         ('NCT1', 'COMPLETED', True, 'https://clinicaltrials.gov/study/NCT1'))

        osf = {'data': [{'attributes': {'title': 'Anxiety', 'date_published': '2026-10-31T18:05:26', 'doi': None,
               'description': 'D', 'tags': ['a']}, 'links': {'html': 'https://osf.io/preprints/psyarxiv/x/'},
               'relationships': {'provider': {'data': {'id': 'psyarxiv'}}}}]}
        r, urls = run(o.osf, osf, 'anxiety', 1, provider='psyarxiv')
        self.check_common(r, 'OSF Preprints', 'preprint')
        self.assertEqual((r[0]['server'], r[0]['doi'], r[0]['published']), ('psyarxiv', '', '2026-10-31'))
        self.assertIn('filter%5Bprovider%5D=psyarxiv', urls[0])
        for bad in ('../x', 'PsyArXiv!', 'a'):
            with self.assertRaises(ValueError):
                o.osf('x', 1, provider=bad)

        eric = {'response': {'docs': [
            {'id': 'ED1', 'title': 'Formative', 'author': ['A'], 'publicationdateyear': 2004, 'peerreviewed': 'F'},
            {'id': 'EJ2', 'title': 'Other', 'peerreviewed': 'T'}, {'id': 'EJ3', 'title': 'Unknown'}]}}
        r, _ = run(o.eric, eric, 'x', 3)
        self.assertEqual([x['peer_reviewed'] for x in r], [False, True, None])
        self.assertEqual(r[0]['url'], 'https://eric.ed.gov/?id=ED1')

        zb = {'result': [{'id': 2675811, 'title': {'title': 'Primes'}, 'year': '1895',
              'contributors': {'authors': [{'name': 'Riemann, B.'}]}, 'zbmath_url': 'https://zbmath.org/2675811'}]}
        r, _ = run(o.zbmath, zb, 'x', 1)
        self.assertEqual((r[0]['title'], r[0]['authors'], r[0]['zbmath_id']), ('Primes', ['Riemann, B.'], '2675811'))

    def test_hal_openaire_chembl_gbif_books(self):
        r, urls = run(o.hal, {'response': {'docs': [{'title_s': ['T'], 'abstract_s': ['A'], 'authFullName_s': ['X Y'],
                      'uri_s': 'https://hal.science/hal-1', 'doiId_s': '10.1/h', 'docType_s': 'ART', 'producedDateY_i': 2015,
                      'journalTitle_s': 'J'}, {'title_s': ['Thesis'], 'docType_s': 'THESE'}]}}, 'x', 2)
        self.check_common(r[:1], 'HAL', 'article')
        self.assertEqual((r[0]['published'], r[0]['journal'], r[1]['kind']), ('2015', 'J', 'repository record'))

        oa = {'results': [{'mainTitle': 'Climate', 'authors': [{'fullName': 'A B'}], 'publicationDate': '2025-01-01',
              'pids': [{'scheme': 'arxiv', 'value': 'z'}, {'scheme': 'doi', 'value': '10.1/oa'}],
              'descriptions': ['d1', 'd2'], 'instances': [{'urls': ['https://x.example/a'], 'refereed': 'nonPeerReviewed'}]},
              {'mainTitle': 'Bare', 'pids': None, 'instances': None, 'authors': None, 'descriptions': None}]}
        r, _ = run(o.openaire, oa, 'x', 2)
        self.check_common(r, 'OpenAIRE', 'article')
        self.assertEqual((r[0]['doi'], r[0]['refereed'], r[0]['abstract'], r[1]['url']), ('10.1/oa', 'nonPeerReviewed', 'd1 d2', ''))

        ch = {'molecules': [{'molecule_chembl_id': 'CHEMBL25', 'pref_name': 'ASPIRIN', 'max_phase': 4.0, 'first_approval': 1950,
              'molecule_type': 'Small molecule', 'molecule_properties': {'full_molformula': 'C9H8O4', 'full_mwt': '180.16'},
              'molecule_structures': {'standard_inchi_key': 'BSYN'}}, {'molecule_chembl_id': 'CHEMBL2', 'pref_name': None,
              'molecule_properties': None, 'molecule_structures': None}]}
        r, _ = run(o.chembl, ch, 'aspirin', 2)
        self.check_common(r, 'ChEMBL', 'compound')
        self.assertEqual((r[0]['molecular_formula'], r[0]['chembl_id'], r[1]['title']), ('C9H8O4', 'CHEMBL25', 'CHEMBL2'))
        with self.assertRaises(ValueError):
            o.chembl('x', 21)

        r, _ = run(o.gbif, {'results': [{'key': 7, 'scientificName': 'Quercus robur', 'rank': 'SPECIES',
                                         'taxonomicStatus': 'ACCEPTED', 'kingdom': 'Plantae', 'family': 'Fagaceae'}]}, 'oak', 1)
        self.check_common(r, 'GBIF', 'taxon')
        self.assertEqual((r[0]['url'], r[0]['taxonomic_status']), ('https://www.gbif.org/species/7', 'ACCEPTED'))

        r, _ = run(o.openlibrary, {'docs': [{'key': '/works/OL1W', 'title': 'Origin', 'author_name': ['Darwin'],
                                              'first_publish_year': 1859, 'publisher': ['P'], 'subject': ['Evolution']}]}, 'x', 1)
        self.check_common(r, 'Open Library', 'book')
        self.assertEqual((r[0]['url'], r[0]['published']), ('https://openlibrary.org/works/OL1W', '1859'))

        books = {'results': [{'id': i, 'title': f'B{i}', 'authors': [{'name': 'Dickens, C'}], 'summaries': ['s'],
                              'subjects': ['Fiction'], 'languages': ['en'], 'copyright': False} for i in (1, 2, 3)]}
        r, _ = run(o.gutenberg, books, 'dickens', 2)
        self.check_common(r, 'Project Gutenberg', 'book')
        self.assertEqual((len(r), r[0]['url']), (2, 'https://www.gutenberg.org/ebooks/1'))

    def test_economics_engineering_data_art_archive_and_encyclopedia(self):
        eb = {'hits': {'hits': [{'id': '1', 'title': 'Inflation', 'creator': ['A'], 'date': ['2026'], 'type': 'book',
              'identifier_url': ['https://example.org/p.pdf'], 'publisher': ['SARB'], 'subject': ['x'], 'series': ['WP 1']},
              {'id': '2', 'title': ['Listed'], 'type': 'article'}]}}
        r, _ = run(o.econbiz, eb, 'inflation', 2)
        self.assertEqual((r[0]['url'], r[0]['kind'], r[1]['url'], r[1]['kind']),
                         ('https://example.org/p.pdf', 'working paper or book', 'https://www.econbiz.de/Record/2', 'article'))

        nt = {'results': [{'id': 19640010635, 'title': 'Hypersonic', 'abstract': 'A', 'stiType': 'PREPRINT',
              'distributionDate': '2019-05-20T00:00:00Z', 'subjectCategories': ['Aeronautics'],
              'authorAffiliations': [{'meta': {'author': {'name': 'Smith, J'}}}, {'meta': {}}]}]}
        r, _ = run(o.ntrs, nt, 'x', 1)
        self.check_common(r, 'NASA NTRS', 'technical report')
        self.assertEqual((r[0]['authors'], r[0]['published'], r[0]['url']),
                         (['Smith, J'], '2019-05-20', 'https://ntrs.nasa.gov/citations/19640010635'))

        dv = {'data': {'items': [{'name': 'Poverty data', 'authors': ['Stanford'], 'published_at': '2015-04-06T00:00:00Z',
              'url': 'https://doi.org/10.7910/DVN/1', 'global_id': 'doi:10.7910/DVN/1', 'description': 'd',
              'name_of_dataverse': 'DV'}]}}
        r, _ = run(o.dataverse, dv, 'poverty', 1)
        self.check_common(r, 'Harvard Dataverse', 'dataset')
        self.assertEqual((r[0]['doi'], r[0]['published'], r[0]['deposit_not_curated']), ('10.7910/DVN/1', '2015-04-06', True))

        r, _ = run(o.artic, {'data': [{'id': 16568, 'title': 'Water Lilies', 'artist_display': 'Claude Monet',
                                       'date_display': '1906', 'medium_display': 'Oil', 'department_title': 'P'}]}, 'monet', 1)
        self.check_common(r, 'Art Institute of Chicago', 'artwork')
        self.assertEqual(r[0]['url'], 'https://www.artic.edu/artworks/16568')

        ia = {'response': {'docs': [{'identifier': 'abc', 'title': 'Voyage', 'creator': 'Darwin', 'year': 1937,
                                     'description': ['d1', 'd2'], 'mediatype': 'texts'}, {'identifier': 'z', 'title': 'Bare'}]}}
        r, urls = run(o.internetarchive, ia, 'darwin', 2)
        self.check_common(r, 'Internet Archive', 'archive item')
        self.assertEqual((r[0]['authors'], r[0]['abstract'], r[0]['user_uploaded_content']), (['Darwin'], 'd1 d2', True))
        self.assertIn('fl%5B%5D=identifier', urls[0])

        r, _ = run(o.wikipedia, {'pages': [{'key': 'Stoicism', 'title': 'Stoicism', 'excerpt': '<span>Stoicism</span> is',
                                            'description': 'Ancient philosophy'}]}, 'stoicism', 1)
        self.check_common(r, 'Wikipedia', 'encyclopedia article')
        self.assertEqual((r[0]['abstract'], r[0]['url']), ('Stoicism is', 'https://en.wikipedia.org/wiki/Stoicism'))

    def test_oeis_medlineplus_reactome_exoplanets(self):
        r, _ = run(o.oeis, [[{'number': 55, 'name': 'Trees', 'data': '1,1,1', 'author': '_N. Sloane_', 'time': '2026-10-17T16:10:24-04:00'}]], '1,2,3', 1)
        self.check_common(r, 'OEIS', 'integer sequence')
        self.assertEqual((r[0]['oeis_id'], r[0]['url']), ('A000055', 'https://oeis.org/A000055'))

        xml = (b'<?xml version="1.0"?><nlmSearchResult><list><document rank="1" url="https://medlineplus.gov/diabetes.html">'
               b'<content name="title">&lt;span&gt;Diabetes&lt;/span&gt;</content>'
               b'<content name="organizationName">NLM</content><content name="FullSummary">&lt;p&gt;Blood sugar.&lt;/p&gt;</content>'
               b'</document></list></nlmSearchResult>')
        r, _ = run(o.medlineplus, xml, 'diabetes', 1)
        self.check_common(r, 'MedlinePlus', 'health topic')
        self.assertEqual((r[0]['title'], r[0]['abstract']), ('Diabetes', 'Blood sugar.'))
        with self.assertRaises(ValueError):
            o.medlineplus('x', 21)

        rc = {'results': [{'typeName': 'Pathway', 'entries': [{'stId': 'R-HSA-109581', 'name': '<span>Apoptosis</span>',
              'exactType': 'Pathway', 'summation': 'Cell death', 'species': ['Homo sapiens']}]}]}
        r, _ = run(o.reactome, rc, 'apoptosis', 3)
        self.check_common(r, 'Reactome', 'pathway')
        self.assertEqual((r[0]['title'], r[0]['url']), ('Apoptosis', 'https://reactome.org/content/detail/R-HSA-109581'))

        ex = [{'pl_name': 'TRAPPIST-1 b', 'hostname': 'TRAPPIST-1', 'disc_year': 2016, 'discoverymethod': 'Transit',
               'pl_orbper': 1.51, 'pl_rade': 1.1, 'pl_masse': 1.0}]
        r, urls = run(o.exoplanets, [ex], "trappist'; drop table x; --", 1)
        self.check_common(r, 'NASA Exoplanet Archive', 'exoplanet')
        self.assertEqual((r[0]['published'], r[0]['host_star']), ('2016', 'TRAPPIST-1'))
        adql = __import__('urllib.parse').parse.parse_qs(urls[0].split('?', 1)[1])['query'][0]
        self.assertEqual(adql.count("'"), 4)
        self.assertNotIn(';', adql)
        with patch('urllib.request.urlopen', side_effect=AssertionError('no request expected')):
            with self.assertRaises(ValueError):
                o.exoplanets("';--", 1)

    def test_wiki_ontology_gene_and_taxon_sources(self):
        r, urls = run(o.wikidata, {'search': [{'id': 'Q1', 'label': 'insulin', 'description': 'hormone',
                      'concepturi': 'http://www.wikidata.org/entity/Q1'}]}, 'insulin', 1)
        self.check_common(r, 'Wikidata', 'knowledge base entity')
        self.assertEqual((r[0]['entity_id'], r[0]['url']), ('Q1', 'http://www.wikidata.org/entity/Q1'))
        self.assertIn('wbsearchentities', urls[0])

        r, _ = run(o.ols, {'response': {'docs': [{'iri': 'http://purl.obolibrary.org/obo/HP_1', 'label': 'Diabetes',
                   'description': ['One.', 'Two.'], 'ontology_name': 'hp', 'obo_id': 'HP:1'}]}}, 'diabetes', 1)
        self.check_common(r, 'Ontology Lookup Service', 'ontology term')
        self.assertEqual((r[0]['abstract'], r[0]['term_id']), ('One. Two.', 'HP:1'))

        r, _ = run(o.mygene, {'hits': [{'_id': '672', 'entrezgene': '672', 'symbol': 'BRCA1', 'name': 'DNA repair', 'summary': 'S'}]}, 'BRCA1', 1)
        self.check_common(r, 'MyGene.info', 'gene')
        self.assertEqual((r[0]['title'], r[0]['url']), ('BRCA1: DNA repair', 'https://www.ncbi.nlm.nih.gov/gene/672'))

        r, _ = run(o.inaturalist, {'results': [{'id': 47851, 'name': 'Quercus', 'rank': 'genus',
                   'preferred_common_name': 'oaks', 'iconic_taxon_name': 'Plantae', 'extinct': False}]}, 'quercus', 1)
        self.check_common(r, 'iNaturalist', 'taxon')
        self.assertEqual((r[0]['common_name'], r[0]['url']), ('oaks', 'https://www.inaturalist.org/taxa/47851'))

        r, urls = run(o.worms, [[{'scientificname': 'Gadus', 'url': 'https:\\/\\/www.marinespecies.org\\/a?id=1', 'rank': 'Genus',
                      'status': 'accepted', 'valid_name': 'Gadus', 'family': 'Gadidae', 'kingdom': 'Animalia'}]], 'Gadus', 1)
        self.check_common(r, 'WoRMS', 'taxon')
        self.assertEqual(r[0]['family'], 'Gadidae')
        self.assertIn('/AphiaRecordsByName/Gadus', urls[0])
        with self.assertRaises(ValueError):
            o.worms('123', 1)

        r, _ = run(o.paleobiodb, {'records': [{'oid': 'txn:38613', 'nam': 'Tyrannosaurus', 'att': 'Osborn 1905', 'noc': 85}]}, 'Tyrannosaurus', 1)
        self.check_common(r, 'Paleobiology Database', 'fossil taxon')
        self.assertTrue(r[0]['url'].endswith('taxon_no=38613'))
        with patch('urllib.request.urlopen', side_effect=AssertionError('no request expected')):
            with self.assertRaises(ValueError):
                o.paleobiodb("x'; drop", 1)

    def test_space_physics_organizations_chemistry_and_texts(self):
        r, _ = run(o.nasaimages, {'collection': {'items': [{'data': [{'title': 'Apollo 11', 'nasa_id': 'a 11', 'date_created': '1969-07-20T00:00:00Z',
                   'description_508': 'Landing', 'media_type': 'image'}]}]}}, 'apollo', 1)
        self.check_common(r, 'NASA Image and Video Library', 'media item')
        self.assertEqual((r[0]['url'], r[0]['published']), ('https://images.nasa.gov/details/a%2011', '1969-07-20'))

        r, _ = run(o.cernopen, {'hits': {'hits': [{'id': 5209, 'metadata': {'title': 'Higgs', 'date_published': '2019', 'doi': None,
                   'type': {'primary': 'Dataset'}, 'abstract': {'description': '<p>Ten events.</p>'}, 'experiment': ['CMS']}}]}}, 'higgs', 1)
        self.check_common(r, 'CERN Open Data', 'dataset')
        self.assertEqual((r[0]['abstract'], r[0]['experiment'], r[0]['url']), ('Ten events.', 'CMS', 'https://opendata.cern.ch/record/5209'))

        r, _ = run(o.ror, {'items': [{'id': 'https://ror.org/052gg0110', 'names': [{'value': 'OU', 'types': ['acronym']},
                   {'value': 'University of Oxford', 'types': ['ror_display']}], 'types': ['funder', 'education'], 'status': 'active',
                   'locations': [{'geonames_details': {'country_name': 'United Kingdom', 'name': 'Oxford'}}],
                   'links': [{'type': 'website', 'value': 'https://www.ox.ac.uk'}]}]}, 'oxford', 1)
        self.check_common(r, 'ROR', 'organization')
        self.assertEqual((r[0]['title'], r[0]['country'], r[0]['website']), ('University of Oxford', 'United Kingdom', 'https://www.ox.ac.uk'))

        r, _ = run(o.chebi, {'results': [{'_source': {'chebi_accession': 'CHEBI:27732', 'name': 'caffeine',
                   'definition': 'An alkaloid.', 'formula': 'C8H10N4O2', 'mass': 194.194}}]}, 'caffeine', 1)
        self.check_common(r, 'ChEBI', 'chemical entity')
        self.assertEqual((r[0]['formula'], r[0]['chebi_id']), ('C8H10N4O2', 'CHEBI:27732'))

        r, _ = run(o.wikisource, {'query': {'search': [{'title': 'Hamlet (Shakespeare)', 'snippet': 'a <span>play</span> &quot;x&quot;',
                   'timestamp': '2026-02-20T10:38:07Z'}]}}, 'hamlet', 1)
        self.check_common(r, 'Wikisource', 'source text')
        self.assertEqual((r[0]['abstract'], r[0]['url']), ('a play "x"', 'https://en.wikisource.org/wiki/Hamlet_%28Shakespeare%29'))

    def test_ecb_returns_latest_observations_and_rejects_odd_series(self):
        data = {'structure': {'name': 'Exchange Rates', 'dimensions': {'observation': [{'values': [{'id': '2026-10-29'}, {'id': '2026-10-30'}]}]}},
                'dataSets': [{'series': {'0:0': {'observations': {'0': [1.113], '1': [1.1172]}}}}]}
        r, urls = run(o.ecb, data, 'EXR/D.USD.EUR.SP00.A', 2)
        self.assertEqual([(x['period'], x['value']) for x in r], [('2026-10-30', 1.1172), ('2026-10-29', 1.113)])
        self.assertEqual((r[0]['dataset'], r[0]['status']), ('Exchange Rates', 'unverified'))
        self.assertIn('/service/data/EXR/D.USD.EUR.SP00.A?', urls[0])
        for bad in ('x', '../x/y', 'EXR/', 'EXR/a b'):
            with self.assertRaises(ValueError):
                o.ecb(bad)
        with self.assertRaisesRegex(ValueError, 'no observations'):
            run(o.ecb, {'dataSets': [{'series': {}}]}, 'EXR/D.USD.EUR.SP00.A')

    def test_funding_public_data_codes_and_indicators(self):
        r, urls = run(o.nsf, {'response': {'award': [{'id': '2611922', 'title': 'Solar grid', 'abstractText': 'Plan.', 'startDate': '01/01/2027',
                      'piFirstName': 'Margaret', 'piLastName': 'Garcia', 'awardeeName': 'Univ'}]}}, 'solar', 1)
        self.check_common(r, 'NSF Awards', 'research grant')
        self.assertEqual((r[0]['authors'], r[0]['url']), (['Margaret Garcia'], 'https://www.nsf.gov/awardsearch/showAward?AWD_ID=2611922'))
        self.assertIn('keyword=solar', urls[0])

        project = {'id': '881226', 'title': 'Solar contacts', 'teaser': 'Cells.', 'startDate': '2019-10-01', 'status': 'CLOSED', 'ecMaxContribution': '2032343.25'}
        for hit in ({'project': project}, [{'project': project}]):
            r, urls = run(o.cordis, {'hits': {'hit': hit}}, "solar' OR 'x", 1)
            self.check_common(r, 'CORDIS', 'funded project')
            self.assertEqual(r[0]['url'], 'https://cordis.europa.eu/project/id/881226')
            self.assertNotIn('%27+OR', urls[0].replace('AND+%27solar+OR+x%27', ''))
        with self.assertRaises(ValueError):
            o.cordis("'';", 1)

        r, _ = run(o.datagovuk, {'result': {'results': [{'id': 'abc', 'title': 'Energy', 'notes': 'N', 'metadata_modified': '2018-12-13T12:54',
                   'organization': {'title': 'Plymouth'}, 'license_title': 'OGL'}]}}, 'energy', 1)
        self.check_common(r, 'data.gov.uk', 'dataset')
        self.assertEqual((r[0]['publisher'], r[0]['url']), ('Plymouth', 'https://www.data.gov.uk/dataset/abc'))

        r, urls = run(o.datosgob, {'result': {'items': [{'_about': 'https://datos.gob.es/catalogo/x', 'title': [{'_value': 'Energia', '_lang': 'es'}],
                      'description': [{'_value': 'Desc', '_lang': 'en'}]}, {'_about': 'https://evil.example/x', 'title': 'T'}]}}, 'a/b', 2)
        self.check_common(r, 'datos.gob.es', 'dataset')
        self.assertEqual((r[0]['title'], r[0]['abstract'], r[1]['url']), ('Energia', 'Desc', ''))
        self.assertIn('/title/a%2Fb?', urls[0])

        r, _ = run(o.icd10cm, [[2, ['E23.2'], None, [['E23.2', 'Diabetes insipidus']]]], 'diabetes', 1)
        self.check_common(r, 'ICD-10-CM', 'diagnosis code')
        self.assertEqual((r[0]['term_id'], r[0]['title']), ('E23.2', 'Diabetes insipidus'))
        r, _ = run(o.icd10cm, [[0, [], None, []]], 'zzz', 1)
        self.assertEqual(r, [])

        r, _ = run(o.sdg, [[{'goal': '1', 'target': '1.1', 'code': '1.1.1', 'description': 'Proportion living below the poverty line', 'tier': '1'},
                    {'goal': '2', 'target': '2.1', 'code': '2.1.1', 'description': 'Prevalence of undernourishment', 'tier': '1'}]], 'POVERTY', 5)
        self.check_common(r, 'UN SDG indicators', 'indicator definition')
        self.assertEqual([x['term_id'] for x in r], ['1.1.1'])

    def test_earthquakes_report_time_and_reject_bad_magnitude(self):
        data = {'features': [{'properties': {'place': 'Vanuatu', 'mag': 6.1, 'time': 1793533623778, 'status': 'reviewed', 'tsunami': 0, 'url': 'https://earthquake.usgs.gov/e'}}]}
        r, urls = run(o.earthquakes, data, 6.0, 1)
        self.assertEqual((r[0]['magnitude'], r[0]['time'], r[0]['status']), (6.1, '2026-11-01T11:47:03Z', 'unverified'))
        self.assertIn('minmagnitude=6.0', urls[0])
        for bad in (-1, 11, 'high', True):
            with self.assertRaises(ValueError):
                o.earthquakes(bad, 1)

    def test_imf_returns_latest_years_and_flags_projections(self):
        year = __import__('datetime').date.today().year
        data = {'values': {'NGDP_RPCH': {'ESP': {str(year - 2): 2.5, str(year - 1): 3.1, str(year + 1): 1.8}}}}
        r, urls = run(o.imf, data, 'esp', 'ngdp_rpch', 2)
        self.assertEqual([(x['year'], x['is_projection']) for x in r], [(str(year + 1), True), (str(year - 1), False)])
        self.assertTrue(urls[0].endswith('/NGDP_RPCH/ESP'))
        for bad in (('Spain', 'NGDP_RPCH'), ('ESP', '../x'), ('all', 'NGDP_RPCH')):
            with self.assertRaises(ValueError):
                o.imf(*bad)
        with self.assertRaisesRegex(ValueError, 'no data'):
            run(o.imf, {'values': {}}, 'ESP', 'NGDP_RPCH')

    def test_law_museums_and_catalogues(self):
        fr = {'results': [{'title': 'Privacy Act Regulations', 'abstract': 'A', 'html_url': 'https://www.federalregister.gov/d/1',
              'publication_date': '2026-09-21', 'type': 'Proposed Rule', 'document_number': '2026-1',
              'agencies': [{'name': 'Treasury Department'}, {'raw_name': 'Office of the Secretary'}]}]}
        r, urls = run(o.federalregister, fr, 'privacy', 1)
        self.check_common(r, 'Federal Register', 'regulatory document')
        self.assertEqual((r[0]['agencies'], r[0]['document_type']), (['Treasury Department', 'Office of the Secretary'], 'Proposed Rule'))
        self.assertIn('conditions%5Bterm%5D=privacy', urls[0])

        r, _ = run(o.clevelandart, {'data': [{'title': 'Red Kerchief', 'creators': [{'description': 'Monet'}],
                   'creation_date': 'c. 1868', 'url': 'https://clevelandart.org/art/1958.39', 'technique': 'oil', 'type': 'Painting'}]}, 'x', 1)
        self.check_common(r, 'Cleveland Museum of Art', 'artwork')
        self.assertEqual((r[0]['authors'], r[0]['published']), (['Monet'], 'c. 1868'))

        r, _ = run(o.vam, {'records': [{'systemNumber': 'O94917', '_primaryTitle': 'Teapot', '_primaryMaker': {'name': 'R. Johnson'},
                   '_primaryDate': '1922', 'objectType': 'Teapot'}, {'systemNumber': 'O2', 'objectType': 'Cup'}]}, 'x', 2)
        self.check_common(r, 'Victoria and Albert Museum', 'museum object')
        self.assertEqual((r[0]['url'], r[1]['title']), ('https://collections.vam.ac.uk/item/O94917/', 'Cup'))

        r, _ = run(o.wellcome, {'results': [{'id': 'h3t6hfqt', 'title': 'Cholera cases', 'workType': {'label': 'Archives'},
                   'referenceNumber': 'PP/1'}]}, 'cholera', 1)
        self.check_common(r, 'Wellcome Collection', 'library or archive item')
        self.assertEqual(r[0]['url'], 'https://wellcomecollection.org/works/h3t6hfqt')

    def test_data_ontology_and_vocabulary_sources(self):
        r, _ = run(o.quickgo, {'results': [{'id': 'GO:0097194', 'name': 'execution phase of apoptosis',
                   'definition': {'text': 'A stage.'}, 'aspect': 'biological_process', 'isObsolete': False}]}, 'apoptosis', 1)
        self.check_common(r, 'Gene Ontology', 'ontology term')
        self.assertEqual((r[0]['abstract'], r[0]['obsolete']), ('A stage.', False))

        eu = {'result': {'results': [{'id': 'trees-wuerzburg', 'title': {'de': 'Bäume', 'en': 'Trees'},
              'description': {'de': 'x'}, 'issued': '2021-02-18T21:09:57Z', 'publisher': {'name': 'Würzburg'}}]}}
        r, _ = run(o.europeandata, eu, 'x', 1)
        self.check_common(r, 'data.europa.eu', 'dataset')
        self.assertEqual((r[0]['title'], r[0]['abstract'], r[0]['published']), ('Trees', 'x', '2021-02-18'))

        dr = {'_embedded': {'stash:datasets': [{'identifier': 'doi:10.5061/dryad.x', 'title': 'Climate',
              'authors': [{'firstName': 'Ana', 'lastName': 'Ruiz'}], 'abstract': '<p>A</p>', 'publicationDate': '2023-01-19'}]}}
        r, _ = run(o.dryad, dr, 'climate', 1)
        self.check_common(r, 'Dryad', 'dataset')
        self.assertEqual((r[0]['doi'], r[0]['authors'], r[0]['abstract']), ('10.5061/dryad.x', ['Ana Ruiz'], 'A'))

        r, _ = run(o.figshare, [[{'title': 'Model', 'doi': '10.1/f', 'url_public_html': 'https://figshare.com/a',
                   'published_date': '2026-11-02T10:34:54Z', 'defined_type_name': 'software'}]], 'x', 1)
        self.check_common(r, 'Figshare', 'software')
        self.assertEqual(r[0]['published'], '2026-11-02')

        r, _ = run(o.mesh, [[{'resource': 'http://id.nlm.nih.gov/mesh/D048909', 'label': 'Diabetes Complications'}]], 'diabetes', 1)
        self.check_common(r, 'MeSH', 'vocabulary term')
        self.assertEqual(r[0]['url'], 'https://meshb.nlm.nih.gov/record/ui?ui=D048909')

        r, _ = run(o.wiktionary, {'pages': [{'key': 'ephemeral', 'title': 'ephemeral', 'excerpt': 'in <b>ephemeral</b>'}]}, 'x', 1)
        self.check_common(r, 'Wiktionary', 'dictionary entry')
        self.assertEqual(r[0]['abstract'], 'in ephemeral')

        bs = {'hits': [{'accession': 'S-EPMC1', 'type': 'study', 'title': 'Cancer', 'author': 'A B C D', 'release_date': '2023-01-01'}]}
        r, _ = run(o.biostudies, bs, 'cancer', 1)
        self.check_common(r, 'BioStudies', 'study')
        self.assertEqual(r[0]['url'], 'https://www.ebi.ac.uk/biostudies/studies/S-EPMC1')

    def test_jstage_reads_atom_with_default_namespace(self):
        xml = (b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:prism="http://prismstandard.org/namespaces/basic/2.0/">'
               b'<entry><article_title><en><![CDATA[Graphene <sub>2</sub>]]></en></article_title>'
               b'<author><en><name>A One</name><name>B Two</name></en></author>'
               b'<material_title><en>Journal of Ceramics</en></material_title><pubyear>2022</pubyear>'
               b'<prism:doi>10.2109/x</prism:doi><title>Graphene <![CDATA[<sub>2</sub>]]></title>'
               b'<article_link><en>https://www.jstage.jst.go.jp/article/x</en></article_link></entry></feed>')
        r, _ = run(o.jstage, xml, 'graphene', 1)
        self.check_common(r, 'J-STAGE', 'article')
        self.assertEqual((r[0]['authors'], r[0]['journal'], r[0]['doi'], r[0]['published']),
                         (['A One', 'B Two'], 'Journal of Ceramics', '10.2109/x', '2022'))

    def test_retractions_finds_notices_for_the_doi_only(self):
        doi = '10.1016/S0140-6736(97)11096-0'
        data = {'message': {'items': [
            {'DOI': '10.1016/s0140-6736(10)60175-4', 'title': ['Retraction'], 'update-to': [
                {'DOI': doi.lower(), 'type': 'retraction', 'label': 'Retraction', 'source': 'retraction-watch',
                 'updated': {'date-time': '2010-02-06T00:00:00Z'}},
                {'DOI': '10.9/other', 'type': 'correction'}]},
            {'DOI': '10.1/n2', 'title': ['Concern'], 'update-to': [{'DOI': doi, 'type': 'expression_of_concern'}]}]}}
        r, urls = run(o.retractions, data, 'https://doi.org/' + doi)
        self.assertTrue(r['retracted'])
        self.assertEqual([n['type'] for n in r['notices']], ['retraction', 'expression_of_concern'])
        self.assertEqual(r['notices'][0]['date'], '2010-02-06')
        self.assertIn('does not prove', r['note'])
        self.assertEqual(r['status'], 'unverified')
        clean, _ = run(o.retractions, {'message': {'items': []}}, doi)
        self.assertEqual((clean['retracted'], clean['notices']), (False, []))
        for bad in ('', 'not a doi', '10.1/'):
            with self.assertRaises(ValueError):
                o.retractions(bad)

    def test_uniprot_pubchem_rcsb(self):
        up = {'results': [{'primaryAccession': 'P01308', 'entryType': 'UniProtKB reviewed (Swiss-Prot)',
              'proteinDescription': {'recommendedName': {'fullName': {'value': 'Insulin'}}},
              'genes': [{'geneName': {'value': 'INS'}}], 'organism': {'scientificName': 'Homo sapiens'},
              'sequence': {'length': 110}},
              {'primaryAccession': 'Q1', 'entryType': 'UniProtKB unreviewed (TrEMBL)',
               'proteinDescription': {'submissionNames': [{'fullName': {'value': 'Sub'}}]}}]}
        r, _ = run(o.uniprot, up, 'insulin', 2)
        self.check_common(r, 'UniProt', 'protein')
        self.assertEqual((r[0]['title'], r[0]['gene'], r[0]['reviewed'], r[1]['title'], r[1]['reviewed']),
                         ('Insulin', 'INS', True, 'Sub', False))

        pc = {'PropertyTable': {'Properties': [{'CID': 2244, 'MolecularFormula': 'C9H8O4', 'MolecularWeight': '180.16',
              'IUPACName': '2-acetyloxybenzoic acid', 'InChIKey': 'BSYNRYMUTXBXSQ-UHFFFAOYSA-N'}]}}
        r, urls = run(o.pubchem, pc, 'aspirin')
        self.assertEqual((r[0]['molecular_formula'], r[0]['url']), ('C9H8O4', 'https://pubchem.ncbi.nlm.nih.gov/compound/2244'))
        with patch('urllib.request.urlopen', side_effect=error.HTTPError('u', 404, 'n', {}, None)):
            with self.assertRaisesRegex(ValueError, 'no compound'):
                o.pubchem('zzzz')

        entry = {'rcsb_id': '4HHB', 'struct': {'title': 'HEMOGLOBIN'}, 'audit_author': [{'name': 'Fermi, G.'}],
                 'rcsb_accession_info': {'initial_release_date': '1984-07-17T00:00:00.000+00:00'},
                 'rcsb_primary_citation': {'pdbx_database_id_DOI': '10.1016/x', 'journal_abbrev': 'J Mol Biol'},
                 'exptl': [{'method': 'X-RAY DIFFRACTION'}], 'rcsb_entry_info': {'resolution_combined': [1.74]}}
        r, urls = run(o.rcsb, [{'result_set': [{'identifier': '4HHB'}]}, entry], 'hemoglobin', 1)
        self.check_common(r, 'RCSB PDB', 'structure')
        self.assertEqual((r[0]['pdb_id'], r[0]['resolution'], r[0]['published'], r[0]['doi']),
                         ('4HHB', 1.74, '1984-07-17', '10.1016/x'))
        self.assertEqual(len(urls), 2)
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'')):
            self.assertEqual(o.rcsb('nothing matches'), [])
        with self.assertRaises(ValueError):
            o.rcsb('x', 11)


class LookupTests(unittest.TestCase):
    def test_preprint_returns_latest_version(self):
        data = {'collection': [{'version': '1', 'title': 'Old', 'doi': '10.1101/2020.03.22.002386'},
                               {'version': '2', 'title': 'A map', 'authors': 'Gordon, D. E.; Jang, G. M.', 'date': '2020-03-27',
                                'doi': '10.1101/2020.03.22.002386', 'server': 'bioRxiv', 'category': 'systems biology',
                                'published': '10.1038/s41586-020-2286-9', 'abstract': 'Abs'}]}
        r, urls = run(o.preprint, data, 'https://doi.org/10.1101/2020.03.22.002386')
        self.assertEqual((r['title'], r['version'], r['authors'], r['kind']), ('A map', '2', ['Gordon, D. E.', 'Jang, G. M.'], 'preprint'))
        self.assertEqual(r['published_version_doi'], '10.1038/s41586-020-2286-9')
        self.assertEqual(r['url'], 'https://www.biorxiv.org/content/10.1101/2020.03.22.002386v2')
        self.assertIn('/details/biorxiv/10.1101/2020.03.22.002386/', urls[0])

    def test_preprint_rejects_other_dois_and_missing_records(self):
        for bad in ('', '10.1038/nature12373', '10.1101/../../etc', 'not a doi'):
            with self.assertRaises(ValueError):
                o.preprint(bad)
        with self.assertRaises(ValueError):
            o.preprint('10.1101/2020.03.22.002386', server='other')
        with self.assertRaisesRegex(ValueError, 'no preprint'):
            run(o.preprint, {'collection': []}, '10.1101/2020.03.22.002386')

    def test_worldbank_rows_and_errors(self):
        data = [{'page': 1, 'lastupdated': '2026-10-08'},
                [{'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'GDP (current US$)'}, 'country': {'id': 'ES', 'value': 'Spain'},
                  'countryiso3code': 'ESP', 'date': '2025', 'value': 1906453309985.88}]]
        r, urls = run(o.worldbank, [data], 'ESP', 'NY.GDP.MKTP.CD', 1)
        self.assertEqual((r[0]['country'], r[0]['year'], r[0]['value'], r[0]['kind']), ('Spain', '2025', 1906453309985.88, 'indicator'))
        self.assertIn('/country/ESP/indicator/NY.GDP.MKTP.CD', urls[0])
        for country, indicator in (('../x', 'NY.GDP.MKTP.CD'), ('ESP', 'a/b'), ('', 'NY.GDP.MKTP.CD'), ('ESP', '')):
            with self.assertRaises(ValueError):
                o.worldbank(country, indicator)
        bad = [{'message': [{'id': '120', 'value': 'Invalid format'}]}]
        with self.assertRaisesRegex(ValueError, 'no data'):
            run(o.worldbank, [bad], 'ESP', 'NOPE.NOPE', 1)


class SafetyTests(unittest.TestCase):
    def test_every_adapter_rejects_empty_queries_and_bad_limits(self):
        for key, item in o.SOURCES.items():
            with self.assertRaises(ValueError, msg=key):
                item['func']('  ', 5)
            with self.assertRaises(ValueError, msg=key):
                item['func']('ok', 0)

    def test_http_errors_become_clear_value_errors(self):
        for code, text in ((429, 'too many requests'), (500, 'HTTP status 500')):
            with patch('urllib.request.urlopen', side_effect=error.HTTPError('u?api_key=s', code, 'x', {}, None)):
                with self.assertRaisesRegex(ValueError, text):
                    o.doaj('x', 1)
        with patch('urllib.request.urlopen', side_effect=error.URLError('offline')):
            with self.assertRaisesRegex(ValueError, 'offline'):
                o.zenodo('x', 1)

    def test_oversize_invalid_json_and_hostile_xml_are_refused(self):
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'x' * (o.MAX_BYTES + 5))):
            with self.assertRaisesRegex(ValueError, 'too large'):
                o.doaj('x', 1)
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'<html>')):
            with self.assertRaisesRegex(ValueError, 'valid JSON'):
                o.doaj('x', 1)
        hostile = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><feed/>'
        with patch('urllib.request.urlopen', return_value=io.BytesIO(hostile)):
            with self.assertRaisesRegex(ValueError, 'DTD'):
                o.arxiv('x', 1)
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'<feed')):
            with self.assertRaisesRegex(ValueError, 'valid XML'):
                o.arxiv('x', 1)

    def test_long_text_is_capped_and_author_lists_truncated(self):
        item = {'id': 'x', 'title': 'T', 'author_display': [f'A{i}' for i in range(100)], 'abstract': 'w ' * 5000}
        r, _ = run(o.plos, {'response': {'docs': [item]}}, 'x', 1)
        self.assertEqual(len(r[0]['authors']), o.AUTHOR_LIMIT)
        self.assertLessEqual(len(r[0]['abstract']), o.ABSTRACT_LIMIT + 3)

    def test_only_https_hosts_with_no_key_in_any_request(self):
        for key, item in o.SOURCES.items():
            self.assertNotIn('api_key', item['about'].lower(), key)
        with patch('urllib.request.urlopen', side_effect=[reply({'results': []})]) as opened:
            o.doaj('x', 1)
        self.assertTrue(opened.call_args[0][0].full_url.startswith('https://'))
        self.assertEqual(opened.call_args[0][0].get_header('User-agent'), o.USER_AGENT)


class WiringTests(unittest.TestCase):
    def run_cli(self, *argv):
        from InvestingOS import cli
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', ['InvestingOS', *argv]), patch('sys.stdout', out), patch('sys.stderr', err):
            try:
                cli.main()
                code = 0
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_list_sources_covers_the_registry_without_network(self):
        with patch('urllib.request.urlopen', side_effect=AssertionError('no network expected')):
            code, out, _ = self.run_cli('list-sources')
        self.assertEqual(code, 0)
        listed = json.loads(out)
        self.assertEqual({row['id'] for row in listed}, set(o.SOURCES))
        self.assertTrue(all(row['api_key'] == 'not needed' for row in listed))

    def test_provider_and_preprints_options_only_apply_to_their_source(self):
        for argv, text in ((('search-source', 'doaj', 'x', '--provider', 'psyarxiv'), '--provider'),
                           (('search-source', 'arxiv', 'x', '--preprints'), '--preprints')):
            code, _, err = self.run_cli(*argv)
            self.assertNotEqual(code, 0)
            self.assertIn(text, err)

    def test_search_source_prints_json_for_a_mocked_source(self):
        data = {'results': [{'id': 'a', 'bibjson': {'title': 'T'}}]}
        with patch('urllib.request.urlopen', side_effect=[reply(data)]):
            code, out, _ = self.run_cli('search-source', 'doaj', 'x', '--limit', '1')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[0]['title'], 'T')

    def test_every_registered_source_is_documented(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        guide = (ROOT / 'docs/research-tools.md').read_text(encoding='utf-8')
        skill = (ROOT / 'skills/InvestingOS/SKILL.md').read_text(encoding='utf-8')
        for key, item in o.SOURCES.items():
            self.assertTrue(f'search-source {key}' in guide, f'guide misses the command for {key}')
            self.assertTrue(item['name'] in guide, f'guide misses the name {item["name"]}')
        for command in ('search-source', 'lookup-preprint', 'worldbank-data', 'imf-data', 'ecb-data', 'usgs-earthquakes', 'check-retraction', 'list-sources'):
            self.assertTrue(command in guide, f'guide misses {command}')
            self.assertTrue(command in skill, f'skill misses {command}')
        self.assertTrue('search-source' in readme, 'README misses search-source')

    def test_professional_notice_is_general_everywhere(self):
        for path in ('README.md', 'docs/user-guide.md', 'skills/InvestingOS/SKILL.md'):
            text = (ROOT / path).read_text(encoding='utf-8')
            self.assertTrue('qualified professional of any kind' in text, f'{path} misses the general statement')
            self.assertTrue('whether or not' in text and 'named here' in text, f'{path} limits itself to listed professionals')
            self.assertTrue('emergency services' in text, f'{path} misses the crisis instruction')
        self.assertTrue('qualified professional of any kind' in (ROOT / 'docs/research-tools.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
