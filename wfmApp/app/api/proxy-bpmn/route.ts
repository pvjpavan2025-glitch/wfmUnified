import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const targetUrl = searchParams.get('url');
    
    if (!targetUrl) {
      return NextResponse.json(
        { error: 'Missing url parameter' },
        { status: 400 }
      );
    }

    // Validate the URL
    let validUrl: URL;
    try {
      validUrl = new URL(targetUrl);
    } catch (error) {
      return NextResponse.json(
        { error: 'Invalid URL format' },
        { status: 400 }
      );
    }

    // Security check - allow localhost, common domains, and CDNs
    const allowedHosts = ['localhost', '127.0.0.1'];
    const allowedDomains = [
      'cdn.staticaly.com',
      'raw.githubusercontent.com', 
      'github.com',
      'gitlab.com',
      'bitbucket.org'
    ];
    
    const isAllowed = allowedHosts.includes(validUrl.hostname) || 
                     validUrl.hostname.endsWith('.local') ||
                     allowedDomains.some(domain => validUrl.hostname === domain || validUrl.hostname.endsWith('.' + domain));
    
    if (!isAllowed) {
      console.warn(`Blocked request to potentially unsafe host: ${validUrl.hostname}`);
      return NextResponse.json(
        { error: `Access to domain '${validUrl.hostname}' is not allowed for security reasons` },
        { status: 403 }
      );
    }

    console.log(`Proxying request to: ${targetUrl}`);

    // Fetch the resource from the target URL
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/xml, text/xml, text/plain, */*',
        'User-Agent': 'BPMN-Modeler-Proxy/1.0',
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { 
          error: `Failed to fetch resource: ${response.status} ${response.statusText}`,
          status: response.status 
        },
        { status: response.status }
      );
    }

    const content = await response.text();
    
    // Validate that we got some content
    if (!content || content.trim().length === 0) {
      return NextResponse.json(
        { error: 'Empty response from target URL' },
        { status: 404 }
      );
    }

    // Return the content with appropriate headers
    return new NextResponse(content, {
      status: 200,
      headers: {
        'Content-Type': 'application/xml',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Cache-Control': 'no-cache',
      },
    });

  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error', 
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

// Handle preflight requests
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
