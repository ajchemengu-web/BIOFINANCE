class ProviderConnection {
  const ProviderConnection({
    required this.providerCode,
    required this.displayName,
    required this.connected,
  });

  final String providerCode;
  final String displayName;
  final bool connected;

  ProviderConnection copyWith({bool? connected}) => ProviderConnection(
        providerCode: providerCode,
        displayName: displayName,
        connected: connected ?? this.connected,
      );
}
