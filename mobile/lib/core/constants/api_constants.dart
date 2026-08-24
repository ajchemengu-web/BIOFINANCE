/// Base URL for the BioFinance backend. Points at localhost for dev; override
/// via --dart-define=API_BASE_URL=... for staging/production builds.
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000/api/v1',
);
