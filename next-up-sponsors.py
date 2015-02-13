#!/usr/bin/env python
for x in [
    {
      "display_name": "Bivio Software",
      "website": "http://www.bivio.biz",
      "logo_filename": "data/bdsc/bivio.gif"
    },
    {
      "display_name": "Market Creation Group",
      "website": "http://marketcreationgroup.com",
      "logo_filename": "data/bdsc/mcg.gif"
    },
    {
      "display_name": "Clifton Larson Allen",
      "website": "http://www.cliftonlarsonallen.com/",
      "logo_filename": "data/bdsc/cliftonlarsonallen.gif"
    },
    {
      "display_name": "Cooley",
      "website": "http://www.cooley.com/broomfield",
      "logo_filename": "data/bdsc/cooley.gif"
    },
    {
      "display_name": "DevelopIntelligence",
      "website": "http://www.developintelligence.com",
      "logo_filename": "data/bdsc/DevelopIntelligence.gif"
    },
    {
      "display_name": "insightsoftware",
      "website": "http://www.insightsoftware.com",
      "logo_filename": "data/bdsc/InsightSoftware.gif"
    },
    {
      "display_name":  "NetFactor",
      "website": "http://www.netfactor.com/",
      "logo_filename": "data/bdsc/netfactor.gif"
    },
    {
      "display_name": "Oracle",
      "website": "http://www.oracle.com",
      "logo_filename": "data/bdsc/oracle_logo.gif"
    },
    {
      "display_name": "PaySimple",
      "website": "http://www.paysimple.com",
      "logo_filename": "data/bdsc/paysimple_logo.gif"
    },
    {
      "display_name": "Ping Identity",
      "website": "http://www.pingidentity.com",
      "logo_filename": "data/bdsc/ping_identity.gif"
    },
    {
      "display_name": "Perkins Coie",
      "website": "http://www.perkinscoie.com/",
      "logo_filename": "data/bdsc/perkins_coie.gif"
    },
    {
      "display_name": "ProLink Solutions",
      "website": "http://www.prolinksolutions.com",
      "logo_filename": "data/bdsc/prolink.gif"
    },
    {
      "display_name": "Rebit",
      "website": "http://www.rebit.com/",
      "logo_filename": "data/bdsc/rebit.gif"
    },
    {
      "display_name": "Sage Law Group",
      "website": "http://www.sagelawgroup.com",
      "logo_filename": "data/bdsc/sagelawgroup.gif"
    },
    {
      "display_name": "Sendgrid",
      "website": "http://www.sendgrid.com/",
      "logo_filename": "data/bdsc/sendgrid.gif"
    },
    {
      "display_name": "Spatial",
      "website": "http://www.spatial.com/",
      "logo_filename": "data/bdsc/ds_spatial.gif"
    },
    {
      "display_name": "Spitfire Group",
      "website": "http://www.spitfiregroup.com",
      "logo_filename": "data/bdsc/spitfirelogo.gif"
    },
    {
      "display_name": "Survey Gizmo",
      "website": "http://www.surveygizmo.com",
      "logo_filename": "data/bdsc/surveygizmo.gif"
    },
    {
      "display_name": "TaxOps",
      "website": "http://www.taxops.com",
      "logo_filename": "data/bdsc/taxops.jpg"
    },
    {
      "display_name": "TrackVia",
      "website": "http://www.trackvia.com",
      "logo_filename": "data/bdsc/trackvia.gif"
    },
    {
      "display_name": "UK Trade & Investment",
      "website": "http://www.ukti.gov.uk/",
      "logo_filename": "data/bdsc/uk_trade_investment.gif"
    }]:
    print("python manage.py --contest next-up --name '{display_name}' --website '{website}' --input_file '{logo_filename}'".format(**x))
