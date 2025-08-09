import React from 'react'
import { Container, Header, SpaceBetween, Box, Link, ColumnLayout } from '@cloudscape-design/components'

function AwsEdgeServices() {
  const services = [
    {
      name: 'AWS WAF',
      description: 'Web Application Firewall that helps protect web applications from common web exploits.',
      link: 'https://aws.amazon.com/waf/'
    },
    {
      name: 'Amazon CloudFront',
      description: 'Content delivery network (CDN) service built for high performance, security, and developer convenience.',
      link: 'https://aws.amazon.com/cloudfront/'
    },
    {
      name: 'AWS Shield',
      description: 'Managed DDoS protection service that safeguards applications running on AWS.',
      link: 'https://aws.amazon.com/shield/'
    },
    {
      name: 'Amazon Route 53',
      description: 'Scalable cloud Domain Name System (DNS) web service.',
      link: 'https://aws.amazon.com/route53/'
    }
  ]

  return (
    <Container>
      <SpaceBetween direction="vertical" size="l">
        <Header variant="h1">☁️ AWS Edge Services</Header>
        
        <Box>
          <p>Learn more about the AWS services used in this bot deception demo:</p>
        </Box>

        <ColumnLayout columns={2}>
          {services.map((service, index) => (
            <Container key={index}>
              <SpaceBetween direction="vertical" size="s">
                <Header variant="h3">{service.name}</Header>
                <Box>
                  <p>{service.description}</p>
                </Box>
                <Link external href={service.link}>
                  Learn more about {service.name}
                </Link>
              </SpaceBetween>
            </Container>
          ))}
        </ColumnLayout>
      </SpaceBetween>
    </Container>
  )
}

export default AwsEdgeServices
