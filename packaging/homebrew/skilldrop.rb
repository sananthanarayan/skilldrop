# Homebrew formula for skilldrop-cli. Lives in the tap repository (sananthanarayan/homebrew-skilldrop)
# as Formula/skilldrop.rb; this copy is the source. Bump with packaging/homebrew/update_formula.py.
class Skilldrop < Formula
  desc "Portable AI-agent skills, measured against the agent without them"
  homepage "https://sananthanarayan.github.io/skilldrop/"
  url "https://registry.npmjs.org/skilldrop-cli/-/skilldrop-cli-0.16.3.tgz"
  sha256 "b070cfb18b8dd19bad91adf6eb049d3c31fc9180cf0fdf542d42b5b016f7db1d"
  license any_of: ["MIT", "Apache-2.0"]

  depends_on "node"

  def install
    system "npm", "install", *std_npm_args
    bin.install_symlink Dir["#{libexec}/bin/*"]
  end

  test do
    assert_match "doc-critique", shell_output("#{bin}/skilldrop list")
  end
end
