import { useNavigate } from 'react-router-dom'

const sections = [
  ['Provider connection issues', 'Symptoms: health check failing. Causes: base URL unreachable/DNS/firewall. Actions: verify URL, run health check, validate TLS/network.'],
  ['Authentication failures', 'Symptoms: 401/403 from provider. Causes: invalid token/secret. Actions: rotate secret ref, check auth type mapping.'],
  ['Mapping/transform errors', 'Symptoms: payload parse/mapping fail. Causes: schema drift. Actions: inspect payload, update mapping rules.'],
  ['Retry/dead-letter failures', 'Symptoms: repeated retries, dead-letter growth. Causes: persistent downstream issues. Actions: resolve root cause then retry manually.'],
  ['PMS webhook debugging', 'Symptoms: missing occupancy/guest/reservation updates. Actions: confirm endpoint delivery and signature validation.'],
  ['Accounting sync debugging', 'Symptoms: PO/invoice sync mismatch. Actions: check entity IDs and currency/tax mapping.'],
  ['BAS/IoT ingestion debugging', 'Symptoms: missing meter readings. Actions: validate device IDs and timestamps/timezone offsets.'],
  ['Email/SMS delivery debugging', 'Symptoms: callback failures/rate limits. Actions: inspect provider callback status and throttling.'],
] as const

export function IntegrationTroubleshootingPage() {
  const navigate = useNavigate()
  return <div className='page full'><div className='glass panel'><h2>Integration Troubleshooting</h2>
    {sections.map(([title, body]) => <div key={title} className='card-section'><h3>{title}</h3><p>{body}</p><div className='row-actions'><button className='button secondary small' onClick={() => navigate('/integrations/status')}>Run health check context</button><button className='button secondary small' onClick={() => navigate('/integrations/jobs')}>Retry failed job context</button></div></div>)}
  </div></div>
}
