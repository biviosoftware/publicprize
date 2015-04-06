// Copyright (c) 2014 bivio Software, Inc.  All rights reserved.

Ladda.bind('button.ladda-button');
$('.pp-tooltip').tooltip({
  'container': 'body'
})

$('.pp-social-icon-click').click(function() {
  open(this.href, '_blank', 'toolbar=0,status=0,width=480,height=360');
  return false;
})

